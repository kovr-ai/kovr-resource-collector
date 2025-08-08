from con_mon_v2.utils.services import ResourceCollectionService

aws_rc_service = ResourceCollectionService('aws')
aws_rc = aws_rc_service.get_resource_collection()
aws_rc_service.validate_resource_field_paths(aws_rc)

github_rc_service = ResourceCollectionService('github')
github_rc = github_rc_service.get_resource_collection()
github_rc_service.validate_resource_field_paths(github_rc)
