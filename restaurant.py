import logging
import numpy as np
from copy import copy
from collections import deque
from datetime import datetime


class Inventory:

    def __init__(self, p, l, t, v, b):
        """Inventory Object which consist of the items in the inventory for the restaurant
        Parameters
        ----------
        p : [int]
            [Number of burger patties.]
        l : [int]
            [Number of Lettuce.]
        t : [int]
            [Number of Tomatoes]
        v : [int]
            [Number of Veggies]
        b : [int]
            [Number of Bacon]
        """
        self.patties = p
        self.lettuce = l
        self.tomato = t
        self.veggie = v
        self.bacon = b

    @classmethod
    def create_from_array(cls, items):
        """Class method to create the inventory object from array.
        Parameters
        ----------
        items : [array]
            [Array of 5 items in the inventory with the format [p,l,t,v,b] 
            example: [100, 200, 200, 100,100] which converts to 100 patties, 200 lettuce, 
            200 tomatoes, 100 veggies and 100 bacons]
        Returns
        -------
        [Inventory]
            [Inventory object]
        """
        if len(items) == 5:
            return cls(*[int(x) for x in items])
        else:
            raise Exception(
                "The length of the items doesnt match with the items in the inventory")

    @classmethod
    def create_from_order_items(cls, items):
        """[Class method to create the inventory object from array of format ['BLT','LT','VLT']]

        Parameters
        ----------
        items : [array]
            [Array of items represented as in the order line 
            example:  ['BLT','LT','VLT'] which converts to 3 patties, 3 lettuce, 3 tomatoes, 1 veggies
            and 1 bacon]
        Returns
        -------
        [Inventory]
            [Inventory object]
        """
        p = len(items)
        item_str = ''.join(items)
        b = item_str.count('B')
        l = item_str.count('L')
        t = item_str.count('T')
        v = item_str.count('V')
        return cls(p, l, t, v, b)

    def as_array(self):
        """Representation of the Inventory object as array

        Returns
        -------
        [numpy array]
            [Numpy Array with the format of [no_of_patties, no_of_lettuce, no_of_tomato, no_of_veggie, no_of_bacon]]
        """
        return np.array([self.patties, self.lettuce, self.tomato, self.veggie, self.bacon])

    def __sub__(self, other_inv):
        """Substract two inventory objects.

        Parameters
        ----------
        other_inv : [Inventory]
            [Inventory object]

        Returns
        -------
        [Inventory]
            [Inventory substrated with the given other inventory object.]
        """
        return self.as_array() - other_inv.as_array()

    def __repr__(self):
        """Representation of the inventory object.

        Returns
        -------
        [string]
        """
        return f"{self.patties},{self.lettuce},{self.tomato},{self.veggie},{self.bacon}"


class Order:
    def __init__(self, restaurant_id, order_time, order_id, items):
        """Order object with the parameters required for the order.

        Parameters
        ----------
        id : [str]
            [Restaurant id of format R1, R2]
        order_time : [str]
            [Order time in the format '%Y-%m-%d %H:%M:%S]
        order_id : [str]
            [Order id of format O1, O2]
        items : [array]
            [inventory items in the format of ['BLT', 'LT', 'VLT']]
        """
        self.restaurant_id = restaurant_id
        order_time = datetime.strptime(order_time, '%Y-%m-%d %H:%M:%S')

        # Easier for debugging.
        # self.order_time = order_time.timestamp() - datetime.strptime("2020-12-08 19:15:31",
        #                                                              '%Y-%m-%d %H:%M:%S').timestamp()
        self.order_time = order_time.timestamp() - datetime.strptime("2020-12-08 19:15:31",
                                                                     '%Y-%m-%d %H:%M:%S').timestamp()
        self.order_id = order_id
        self.items = items
        self.inventory_req = Inventory.create_from_order_items(items)
        self.required_time = 0
        self.status = None

    @classmethod
    def create_from_line(cls, line):
        """Create order from line of format R1,2020-12-08 19:15:31,O1,BLT,LT,VLT
        Parameters
        ----------
        line : [str]
            [Line of order of format "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"]
        Returns
        -------
        [Order]
            [Order object]
        """
        line = line.strip()
        line = line.split(',')
        return cls(*line[:3], line[3:])

    def __repr__(self):
        """Representation of the inventory object.
        Also converts the required time represented in the secs to mins
        Returns
        -------
        [string]
        """
        req_time = f",{int(self.required_time / 60)}" if self.status == 'ACCEPTED' else ''
        return f"{self.restaurant_id},{self.order_id},{self.status}{req_time}"


class Department:
    def __init__(self, name: str, capacity: int, task_time: int):
        """Initialize different department of the kitchen
        We use the queue to store the current status of the department and cache to
        check if the order is possible within the 20 mins of time and if the inventory 
        is enough to complete the order. If the order is not possible we revert the cache to
        queue and if the order is possible we commit the cache to queue.
        Parameters
        ----------
        name : [string]
            [Name of th department.]
        capacity : [int]
            [Capacity of the department.]
        task_time : [int]
            [Time it takes to complete a task in secs.]
        """
        self.name = name
        self.capacity = capacity
        self.task_time = task_time

        # queue which contains the end time for each item in the order list.
        self.queue = [deque(maxlen=1) for i in range(self.capacity)]
        self.cache = [deque(maxlen=6) for i in range(self.capacity)]

    def append_time(self, order_time):
        """Append the order_time + task_time + wait_time to the cache.

        Parameters
        ----------
        order_time : [int]
            [Time represented in epochs.]

        Returns
        -------
        [int]
            [required time to complete including the waiting time]
        """
        # find the queue which is going to be finished latest.
        # or the get the queue with the least echo time.
        cache = min(self.cache)

        # find the waiting time.
        wait_time = 0
        if len(cache):
            wait_time = max((cache[0] - order_time), 0)
        # append the time required including the waiting time in epochs
        cache.appendleft(order_time + self.task_time + wait_time)

        return self.task_time + wait_time

    def required_time(self, order: Order):
        """Calculate the required time for the order.
        Iterates over the items in the order and calculates the time required.
        Parameters
        ----------
        order : Order
            [Order object]

        Returns
        -------
        [int]
            [Time required for the order in secs.]
        """
        req_time = 0
        for item in order.items:
            item_req_time = self.append_time(order.order_time)
            logging.debug(f"{item_req_time} sec required for {item} item.")
            req_time = max(req_time, item_req_time)
        logging.info(
            f"{req_time} sec required for {order.order_id} order in {self.name}")
        return req_time

    def commit_required_time(self):
        """Save the required time from the cache to queue.
        """
        self.queue = []
        for cache in self.cache:
            if len(cache):
                self.queue.append(copy(cache))
            else:
                self.queue.append(deque(maxlen=1))
        # self.cache = self.queue

    def reverse_required_time(self):
        """Reset the cache to the value of the queue because of 
        cancellation of the order.
        """
        self.cache = copy(self.queue)


class Restaurant:

    def __init__(self, id, depts, inv):
        """Restaurant with id and list of Departments and current Inventory.

        Parameters
        ----------
        id : [str]
            [restaurant id]
        depts : [list of Department]
            [List of departments in the restaurant]
        inv : [Inventory]
            [Current inventory of the restaurant]
        """
        self.id = id
        self.departments = depts
        self.inventory = inv

        self.total_time = 0
        self.cache_inventory = None

    def check_inventory(self, order:Order):
        """Check the inventory is valid of the given order.

        Parameters
        ----------
        order : [Order]
            [Order object]

        Returns
        -------
        [Boolean]
            [If the inventory is enough return True else return False]
        """
        self.cache_inventory = self.inventory - order.inventory_req
        logging.info(f"--- REMAINING INVENTORY : {self.cache_inventory}")
        if min(self.cache_inventory) < 0:
            return False
        return True

    def required_time(self, order):
        """Calculate the required time for the order is valid.
        Parameters
        ----------
        order : [Order]
            [Order object]
        Returns
        -------
        [Int]
            [Required time for the order]
        """
        req_time = 0
        # cache = None
        for d in self.departments:
            req_time += d.required_time(order)
            # req_time += d.required_time(order, cache)
            # cache = d.cache
        logging.info(
            f"--- TOTAL {req_time} sec required for the {order.order_id}. ----")
        return req_time

    def commit_required_time(self):
        """Save the required time in the departments"""
        for d in self.departments:
            d.commit_required_time()

    def reverse_required_time(self):
        """Reverse the required time in the departments"""
        for d in self.departments:
            d.reverse_required_time()

    def commit_inventory(self):
        """Save the inventory"""
        self.inventory = Inventory.create_from_array(self.cache_inventory)

    def check_order(self, order: Order, time_threshold):
        """Check if the order is valid

        Parameters
        ----------
        order : Order
            [New order that is made in the restaurant.]
        time_threshold : [int]
            [Time threshold in secs.]

        Returns
        -------
        [Order]
            [Description if the order with its status]
        """
        # CHECK THE INVENTORY FOR THE ORDER.
        if self.check_inventory(order):
            # CALCULATE THE TIME REQUIRED FOR THE ORDER.
            req_time = self.required_time(order)
            if req_time < time_threshold:
                self.commit_inventory()
                self.commit_required_time()
                self.total_time += req_time
                order.status = 'ACCEPTED'
                order.required_time = req_time

            else:
                order.status = 'REJECTED'
                self.reverse_required_time()
                logging.warning(f"Order Canceled due to insufficient time")
        else:
            order.status = 'REJECTED'
            logging.warning(f"Order Canceled due to insufficient inventory")
        return order

    @classmethod
    def create_from_line(cls, line):
        """Create the restaurant from a line of format
        R1,4C,1,3A,2,2P,1,100,200,200,100,100

        Parameters
        ----------
        line : [str]
            [string with the format R1,4C,1,3A,2,2P,1,100,200,200,100,100]

        Returns
        -------
        [Restaurant]
            [restaurant object]

        Raises
        ------
        Exception
            [If the format of the line is not good.]
        """
        try:
            line = line.strip()
            line = line.split(',')

            # ID
            restaurant_id = line[0]

            # DEPARTMENTS
            c_dept = Department('cooking', int(
                line[1].replace('C', '')), int(line[2])*60)
            a_dept = Department('asembling', int(
                line[3].replace('A', '')), int(line[4])*60)
            p_dept = Department('packaging', int(
                line[5].replace('P', '')), int(line[6])*60)
            departments = [c_dept, a_dept, p_dept]

            # INVENTORY
            inventory = Inventory.create_from_array(line[7:])

            return cls(restaurant_id, departments, inventory)
        except Exception as e:
            raise Exception(
                f"Could not create the restaurant from the line! \n{e}")

    def __repr__(self):
        """Representation of the restaurant object.

        Returns
        -------
        [type]
            [description]
        """
        return f"{self.id},TOTAL,{int(self.total_time/60)}\n{self.id},INVENTORY,{self.inventory}"


if __name__ == "__main__":

    logging.basicConfig(level=logging.ERROR)
    input_file = open("input.txt", 'r')

    # todo assumption that there is only one line to input the restaurant information.
    # todo check the line format and accordint to it create multiple restaurant
    line = input_file.readline()
    # CREATE RESTAURANT.
    restaurant = Restaurant.create_from_line(line)
    # for multiple restaurants.
    restaurants = {restaurant.id: restaurant}

    # within 20 mins
    time_threshold = 21 * 60
    for line in input_file.readlines():

        # CREATE ORDER FROM THE LINE.
        order = Order.create_from_line(line)
        # CHECK THE ORDER CAN BE TAKEN FROM THE RESTAURANT.
        restaurant = restaurants[order.restaurant_id]
        order = restaurant.check_order(order, time_threshold)
        print(order)
    print(restaurant)
