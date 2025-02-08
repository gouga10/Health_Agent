from multiprocessing import Process, Manager
import main
import streamlit

if __name__ == "__main__":
    manager = Manager()
    shared_queue = manager.Queue()

    p1 = Process(target=streamlit.producer, args=(shared_queue,))
    p2 = Process(target=main.consumer, args=(shared_queue,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
