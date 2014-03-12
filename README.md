Overview

* **check_for_inactivity** is used run periodically to check whether the mediacenter is doing something important or should be shut down
* **find_next_recording_time** is called whenever the scheduler is run by mythtv. It will find the next recording and send the wakeuptime to the server.
* **update_program** is used to fetch the program from ontv.dk and update the database
