from frappe.utils.background_jobs import get_workers, get_queue_list, get_queue
from agarwals.utils.error_handler import log_error
import os

def __add(count, queue="cg_queue"):
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
        current_workers = get_workers(get_queue(queue))
        multi_queue_worker = 0
        for worker in current_workers:
            if len(worker.queue_names()) > 1:
                multi_queue_worker+=1
        dedicated_worker_count = len(current_workers) - multi_queue_worker
        if dedicated_worker_count >= count:
            log_error(f"The count you have provided {count} must be higher than the worker count is {dedicated_worker_count} that is already in the system")
            return None
        worker_to_add = count - dedicated_worker_count
        for i in range(worker_to_add):
            os.system(f"bench worker --queue {queue} --burst &")
    except Exception as e:
        log_error(f"Error in Adding Worker: {e}")

def add_workers(worker_count_dict):
    for queue,count in worker_count_dict.items():
        __add(count, queue)

def get_worker_dict(worker_count, queue, worker_count_dict):
    if queue not in worker_count_dict.keys():
        worker_count_dict[queue] = int(worker_count)
    else:
        worker_count_dict[queue] += int(worker_count)
    return worker_count_dict