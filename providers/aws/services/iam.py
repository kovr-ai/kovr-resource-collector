from providers.service import BaseService, service_class
import boto3

@service_class
class IAMService(BaseService):
    def __init__(self, client: boto3.Session):
        super().__init__(client)

    def process(self):
        data = {
            "account": {
                "summary": {},
                "password_policy": {},
                "credential_report": {}
            },
            "users": {},
            "groups": {},
            "roles": {},
            "policies": {},
            "relationships": {
                "user_groups": {},
                "group_users": {},
                "user_policies": {},
                "group_policies": {},
                "role_policies": {}
            }
        }
        
        client = self.client.client("iam")
        
        try:
            data["account"]["summary"] = client.get_account_summary()["SummaryMap"]
        except Exception as e:
            data["account"]["summary"] = {}
        
        try:
            data["account"]["password_policy"] = client.get_account_password_policy()
        except Exception as e:
            data["account"]["password_policy"] = {}
        
        try:
            data["account"]["credential_report"] = self._get_credential_report(client)
        except Exception as e:
            data["account"]["credential_report"] = {}
        
        try:
            paginator = client.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    username = user["UserName"]
                    data["users"][username] = {
                        "arn": user["Arn"],
                        "user_id": user["UserId"],
                        "create_date": user["CreateDate"].isoformat(),
                        "path": user["Path"],
                        "access_keys": [],
                        "mfa_devices": [],
                        "login_profile": None
                    }
                    
                    try:
                        keys_response = client.list_access_keys(UserName=username)
                        data["users"][username]["access_keys"] = keys_response["AccessKeyMetadata"]
                    except Exception as e:
                        data["users"][username]["access_keys"] = {}

                    try:
                        mfa_response = client.list_mfa_devices(UserName=username)
                        data["users"][username]["mfa_devices"] = mfa_response["MFADevices"]
                    except Exception as e:
                        data["users"][username]["mfa_devices"] = {}
                    
                    try:
                        login_profile = client.get_login_profile(UserName=username)
                        data["users"][username]["login_profile"] = login_profile["LoginProfile"]
                    except client.exceptions.NoSuchEntityException:
                        data["users"][username]["login_profile"] = None
                    except Exception as e:
                        data["users"][username]["login_profile"] = {}
        except Exception as e:
            data["users"] = {}
        
        try:
            paginator = client.get_paginator('list_groups')
            for page in paginator.paginate():
                for group in page['Groups']:
                    groupname = group["GroupName"]
                    data["groups"][groupname] = {
                        "arn": group["Arn"],
                        "group_id": group["GroupId"],
                        "create_date": group["CreateDate"].isoformat(),
                        "path": group["Path"]
                    }
        except Exception as e:
            data["groups"] = {}
        
        try:
            paginator = client.get_paginator('list_roles')
            for page in paginator.paginate():
                for role in page['Roles']:
                    rolename = role["RoleName"]
                    data["roles"][rolename] = {
                        "arn": role["Arn"],
                        "role_id": role["RoleId"],
                        "create_date": role["CreateDate"].isoformat(),
                        "path": role["Path"],
                        "assume_role_policy_document": role["AssumeRolePolicyDocument"],
                        "instance_profiles": []
                    }
                    
                    try:
                        profiles_response = client.list_instance_profiles_for_role(RoleName=rolename)
                        data["roles"][rolename]["instance_profiles"] = profiles_response["InstanceProfiles"]
                    except Exception as e:
                        data["roles"][rolename]["instance_profiles"] = {}
        except Exception as e:
            data["roles"] = {}
        
        try:
            paginator = client.get_paginator('list_policies')
            for page in paginator.paginate(Scope='Local'):
                for policy in page['Policies']:
                    policy_arn = policy["Arn"]
                    data["policies"][policy_arn] = {
                        "policy_name": policy["PolicyName"],
                        "policy_id": policy["PolicyId"],
                        "create_date": policy["CreateDate"].isoformat(),
                        "update_date": policy["UpdateDate"].isoformat(),
                        "path": policy["Path"],
                        "default_version_id": policy["DefaultVersionId"],
                        "attachment_count": policy["AttachmentCount"],
                        "default_version": None
                    }
                    
                    # Get policy version content
                    try:
                        version_response = client.get_policy_version(
                            PolicyArn=policy_arn,
                            VersionId=policy["DefaultVersionId"]
                        )
                        data["policies"][policy_arn]["default_version"] = version_response["PolicyVersion"]
                    except Exception as e:
                        data["policies"][policy_arn]["default_version"] = {}
        except Exception as e:
            data["policies"] = {}
        
        self._build_relationships(client, data)
        
        return data
    
    def _build_relationships(self, client, data):
        if "users" in data and not isinstance(data["users"], dict):
            return
            
        for username in data["users"]:
            try:
                groups_response = client.list_groups_for_user(UserName=username)
                group_names = [group["GroupName"] for group in groups_response["Groups"]]
                data["relationships"]["user_groups"][username] = group_names
                
                for group_name in group_names:
                    if group_name not in data["relationships"]["group_users"]:
                        data["relationships"]["group_users"][group_name] = []
                    data["relationships"]["group_users"][group_name].append(username)
            except Exception as e:
                data["relationships"]["user_groups"][username] = {}
        
        for username in data["users"]:
            try:
                policies_response = client.list_user_policies(UserName=username)
                inline_policies = policies_response["PolicyNames"]
                
                attached_policies = client.list_attached_user_policies(UserName=username)
                attached_policy_arns = [policy["PolicyArn"] for policy in attached_policies["AttachedPolicies"]]
                
                data["relationships"]["user_policies"][username] = {
                    "inline": inline_policies,
                    "attached": attached_policy_arns
                }
            except Exception as e:
                data["relationships"]["user_policies"][username] = {}
        
        for groupname in data["groups"]:
            try:
                policies_response = client.list_group_policies(GroupName=groupname)
                inline_policies = policies_response["PolicyNames"]
                
                attached_policies = client.list_attached_group_policies(GroupName=groupname)
                attached_policy_arns = [policy["PolicyArn"] for policy in attached_policies["AttachedPolicies"]]
                
                data["relationships"]["group_policies"][groupname] = {
                    "inline": inline_policies,
                    "attached": attached_policy_arns
                }
            except Exception as e:
                data["relationships"]["group_policies"][groupname] = {}
        
        for rolename in data["roles"]:
            try:
                policies_response = client.list_role_policies(RoleName=rolename)
                inline_policies = policies_response["PolicyNames"]
                
                attached_policies = client.list_attached_role_policies(RoleName=rolename)
                attached_policy_arns = [policy["PolicyArn"] for policy in attached_policies["AttachedPolicies"]]
                
                data["relationships"]["role_policies"][rolename] = {
                    "inline": inline_policies,
                    "attached": attached_policy_arns
                }
            except Exception as e:
                data["relationships"]["role_policies"][rolename] = {}
    
    def _get_credential_report(self, client):
        try:
            try:
                client.generate_credential_report()
            except client.exceptions.LimitExceededException:
                pass
            
            response = client.get_credential_report()
            return {
                "generated_time": response["GeneratedTime"].isoformat(),
                "report_format": response["ReportFormat"],
                "content": response["Content"].decode('utf-8')
            }
        except Exception as e:
            return {}