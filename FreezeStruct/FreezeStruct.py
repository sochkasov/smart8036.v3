# coding=utf8
import itertools


class FreezeStruct(object):
    stack_size_max = 7
    stack_lifo = list(dict())
    stack_check_ready = False

    def __init__(self):
        self.stack_lifo = list(dict())
        return

    def add(self, cur_dict):
        self.stack_lifo.append(cur_dict)
        self.get()
        return True

    def is_freeze(self):
        if self.stack_check_ready:
            stack_cur = self.stack_lifo[0]
            for stack in self.stack_lifo:
                if stack != stack_cur:
                    return False
            return True
        return False


    def get(self):
        if len(self.stack_lifo) > self.stack_size_max:
            # Дошли до максимального размера стека.
            # Теперь будем проверять
            self.stack_check_ready = True
            # И теперь будем удалять из стеке старые записи
            self.stack_lifo.pop(0)
        return self.stack_lifo