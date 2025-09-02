BEGIN;

-- Move checks
TRUNCATE checks_bkp;
INSERT INTO checks_bkp SELECT * FROM checks;
TRUNCATE checks;

-- Move con_mon_results
TRUNCATE con_mon_results_bkp;
INSERT INTO con_mon_results_bkp SELECT * FROM con_mon_results;
TRUNCATE con_mon_results;

-- Move con_mon_results_history
-- TRUNCATE con_mon_results_history_bkp;
-- INSERT INTO con_mon_results_history_bkp SELECT * FROM con_mon_results_history;
TRUNCATE con_mon_results_history;

COMMIT;
