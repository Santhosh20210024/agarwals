from frappe.utils.background_jobs import get_workers, get_queue_list, get_queue, get_redis_conn
from agarwals.utils.error_handler import log_error
import os
from rq.command import send_shutdown_command

def add(count, queue="cg_queue"):
    try:
        default_queue_list = get_queue_list()
        if queue not in default_queue_list:
            log_error(f"There is no queue named {queue} to start a worker and it should be in the following list {', '.join(default_queue_list)}")
            return None
        try:
            count = int(count)
        except Exception as e:
            log_error(f"Please Pass the correct Count {e}")
            return None
        current_worker = get_workers(get_queue(queue))
        worker_count = len(current_worker)
        if worker_count >= count:
            log_error(f"The count you have provided {count} must be higher than the worker count is {worker_count} that is already in the system")
            return None
        worker_to_add = count - worker_count
        for i in range(worker_to_add):
            os.system(f"bench worker --queue {queue} --burst &")
    except Exception as e:
        log_error(f"Error in Adding Worker: {e}")