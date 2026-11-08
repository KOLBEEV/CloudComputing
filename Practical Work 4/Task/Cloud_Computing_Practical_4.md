# Cloud Computing · Practical 4
## Backup and Recovery of a Cloud Service

**Objective.** Find out which registration records survive container replacement and which can be recovered after storage loss. Measure recovery time and the age of the recovered data.

### Task 1. Build the CourseHub image

Extract the source files in the VM and open the directory containing the Dockerfile. If the base image is absent, put the supplied `python-3.12-slim.tar` in the same directory. Build the image from source:

```bash
docker image inspect python:3.12-slim >/dev/null 2>&1 || docker load -i python-3.12-slim.tar
docker build --pull=false --network=none -t coursehub-pz3:1 .
docker image inspect coursehub-pz3:1 --format '{{.Id}} {{.Architecture}}'
```

Save the output of the last command. Briefly explain what `FROM`, `WORKDIR`, `COPY`, and `CMD` do.

### Task 2. Replace the container

1. Start CourseHub. Save the container ID and the name of the mounted volume.
2. Create two registrations through the API. Use the synthetic student IDs **A** and **B** and the same course ID, **CC101**. Save the API response listing the two registrations.
3. Replace the container using the same volume. Record the new container ID and verify that the volume name is unchanged.
4. List the registrations again. Check whether A and B are still present.

### Task 3. Back up SQLite and add another registration

1. Use the supplied backup command to create a consistent SQLite snapshot. Record the path and the snapshot time (`t_backup`). Keep writes paused during the backup so the snapshot time is unambiguous.
2. Verify that the backup exists outside the Docker volume. Save its size and SHA-256 checksum, and record the result of SQLite's integrity check.
3. Create registration **C** for course **CC101** after the snapshot. Save its creation time and the API response showing all three registrations.

### Task 4. Simulate storage loss

1. Record `t_failure` immediately before stopping CourseHub to simulate the incident. Use the same VM clock and time zone for all timestamps.
2. Remove the lab container and delete its dedicated volume using the lab command. Verify the volume is gone and the backup file still exists.
3. Start CourseHub with a new, empty volume. Save the HTTP status and response from the registrations endpoint. A successful response with an empty list confirms the API is reachable and the original records are missing.

### Task 5. Restore and verify

1. Stop the service and restore the SQLite snapshot into the replacement volume. Start CourseHub again.
2. Query the registrations endpoint. Verify that **A and B are present and C is absent**. Record `t_recovered` after the first API response that confirms the restored data. Save the HTTP status and response body.
3. Calculate the following. Include the time spent on the empty-volume check in the recovery interval.

| Measure | Calculation | Lab target |
| --- | --- | --- |
| Observed recovery time | `t_recovered − t_failure` | RTO ≤ 10 minutes |
| Age of the restored snapshot at failure | `t_failure − t_backup` | RPO ≤ 5 minutes |
| Lost registrations | Compare the list before failure with the restored list | Record the missing IDs |

Report whether the measured values meet the lab targets. Explain how the timing of the backup affects the RPO result. If you miss a target, report the actual measurement and explain what contributed to it.

### Task 6. Submit your report

Submit an individual English report named `CC_PZ3_Surname_Group.pdf` (approximately 2–3 pages). Include your name, group, date, guest OS and Docker version, a small diagram showing the API, volume and backup location, and the commands you used. Record the build command, image ID and architecture. Complete the table with your actual results and point to the corresponding command output or API response.

| Checkpoint | HTTP status | Registration IDs observed | Evidence |
| --- | --- | --- | --- |
| Before replacing the container | | | |
| After replacing the container | | | |
| After creating registration C | | | |
| After starting with an empty volume | | | |
| After restoring the backup | | | |

Include the three timestamps, recovery calculations, and backup verification. In a short conclusion, explain why A and B survived container replacement, why C was absent after recovery, and what would happen to the backup if the VM disk were lost.

Stop the lab at the end. Keep the report, saved evidence and backup until the work is graded.
