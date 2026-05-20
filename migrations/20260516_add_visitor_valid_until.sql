ALTER TABLE visitors
  ADD COLUMN valid_until timestamp NULL DEFAULT NULL AFTER status;

UPDATE visitors
SET valid_until = CAST(CONCAT(DATE(COALESCE(visitor_last_updated, NOW())), ' 23:59:59') AS DATETIME)
WHERE valid_until IS NULL;

UPDATE users u
JOIN visitors v ON u.user_id = v.user_id
SET u.active = 0,
    v.status = 'Outside'
WHERE u.role = 'visitor'
  AND COALESCE(u.active, 1) = 1
  AND v.valid_until IS NOT NULL
  AND v.valid_until < NOW();
