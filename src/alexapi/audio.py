import Queue


class AudioQueueManager(object):
    """
    Build a queue of audio file for play sequencially 
    """
    q = Queue.Queue()

    def addItem(self, item):
        self.q.put(item)

    def getNextItem(self):
        if not self.q.empty():
            return self.q.get()
        else:
            return -1
        
    def getItemCount(self):
        return self.q.qsize()


