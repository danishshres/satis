import unittest

import numpy as np
from mock import Mock, patch

from restaurant import Inventory, Order, Department, Restaurant


class InventoryTest(unittest.TestCase):

    def test_create_from_array(self):

        array = [100, 200, 200, 100, 100]
        inv = Inventory.create_from_array(array)

        self.assertEqual(inv.patties, 100)
        self.assertEqual(inv.lettuce, 200)
        self.assertEqual(inv.tomato, 200)
        self.assertEqual(inv.veggie, 100)
        self.assertEqual(inv.bacon, 100)

        with self.assertRaises(Exception):
            inv = Inventory.create_from_array([1, 2, 3])

    def test_create_from_order_items(self):
        # test 1
        order_items = ['BLT', 'LT', 'VLT']
        inv = Inventory.create_from_order_items(order_items)
        self.assertEqual(inv.patties, 3)
        self.assertEqual(inv.lettuce, 3)
        self.assertEqual(inv.tomato, 3)
        self.assertEqual(inv.veggie, 1)
        self.assertEqual(inv.bacon, 1)

        # test 2
        order_items = ['BLT', 'LT', 'LT']
        inv = Inventory.create_from_order_items(order_items)
        self.assertEqual(inv.patties, 3)
        self.assertEqual(inv.lettuce, 3)
        self.assertEqual(inv.tomato, 3)
        self.assertEqual(inv.veggie, 0)
        self.assertEqual(inv.bacon, 1)
        # self.assertEqual(inv, [100, 200, 200, 100, 100])

        # test 3
        order_items = []
        inv = Inventory.create_from_order_items(order_items)
        self.assertEqual(inv.patties, 0)
        self.assertEqual(inv.lettuce, 0)
        self.assertEqual(inv.tomato, 0)
        self.assertEqual(inv.veggie, 0)
        self.assertEqual(inv.bacon, 0)

    def test_as_array(self):
        # test 1
        order_items = ['BLT', 'LT', 'LT']
        inv = Inventory.create_from_order_items(order_items)
        ary = inv.as_array()
        self.assertListEqual(list(ary), [3, 3, 3, 0, 1])

        # test 2
        array = [100, 200, 200, 100, 100]
        inv = Inventory.create_from_array(array)
        ary = inv.as_array()
        self.assertListEqual(list(ary), array)

    def test_substraction(self):
        array = [100, 100, 100, 100, 100]
        inv_1 = Inventory.create_from_array(array)
        array = [1, 2, 3, 4, 5]
        inv_2 = Inventory.create_from_array(array)

        diff_ary = inv_1 - inv_2
        self.assertListEqual(list(diff_ary), [99, 98, 97, 96, 95])

    def test_repr(self):
        array = [99, 98, 97, 96, 95]
        inv_1 = Inventory.create_from_array(array)
        self.assertEqual(str(inv_1), '99,98,97,96,95')


class OrderTest(unittest.TestCase):

    def test_create_from_line(self):
        # test 1
        line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
        with patch.object(Inventory, 'create_from_order_items', return_value='TESTING') as mock_method:
            order = Order.create_from_line(line)

            self.assertEqual(order.restaurant_id, 'R1')
            self.assertEqual(order.order_time, 0)
            self.assertEqual(order.order_id, 'O1')
            self.assertEqual(order.required_time, 0)
            self.assertEqual(order.status, None)

            # We have already tested the inventory class.
            self.assertEqual(order.inventory_req, 'TESTING')

    def test_repr(self):
        # test1
        line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
        with patch.object(Inventory, 'create_from_order_items', return_value='TESTING') as mock_method:
            order = Order.create_from_line(line)
            self.assertEqual(str(order), "R1,O1,None")

            # test 2
            order.status = 'ACCEPTED'
            order.required_time = 60
            self.assertEqual(str(order), "R1,O1,ACCEPTED,1")


class DepartmentTest(unittest.TestCase):

    def test_init(self):
        dept = Department('cooking', 4, 60)
        self.assertEqual(dept.name, 'cooking')
        self.assertEqual(dept.capacity, 4)
        self.assertEqual(dept.task_time, 60)

        self.assertEqual(len(dept.queue), 4)
        self.assertEqual(len(dept.cache), 4)

    def test_append_time(self):
        dept = Department('cooking', 4, 60)
        # test1
        req_time = dept.append_time(0)
        self.assertEqual(req_time, 60)

        # test 2
        # now lets add another 3 items so that the cooking
        # dept is full of job
        req_time = dept.append_time(0)
        req_time = dept.append_time(0)
        req_time = dept.append_time(0)
        # it should still take 60 secs cause they can work paralle
        self.assertEqual(req_time, 60)

        # test 3
        # now lets add another 1 item
        # not since the dept is full of task it should wait of 60 secs
        # for the previous task to be completed and then take another 60 sec
        # for the given task to be completed
        req_time = dept.append_time(0)
        self.assertEqual(req_time, 120)

        # test 4
        # now lets add another 1 item after 30 secs i.e its like
        # a new order that arrived after 30secs.
        req_time = dept.append_time(30)
        self.assertEqual(req_time, 90)

    def test_required_time(self):
        dept = Department('cooking', 4, 60)

        # test1
        line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
        order = Order.create_from_line(line)
        req_time = dept.required_time(order)
        self.assertEqual(req_time, 60)

        # test2
        line = "R1,2020-12-08 19:15:32,O2,VLT,VT,BLT,LT,VLT"
        order = Order.create_from_line(line)
        req_time = dept.required_time(order)
        self.assertEqual(req_time, 120)

    def test_commit_required_time(self):
        dept = Department('cooking', 4, 60)
        dept.commit_required_time()
        self.assertEqual(dept.cache, dept.queue)

        dept.cache = None
        self.assertNotEqual(dept.cache, dept.queue)

    def test_reverse_required_time(self):
        dept = Department('cooking', 4, 60)
        # add the append time
        req_time = dept.append_time(0)
        self.assertNotEqual(dept.cache, dept.queue)

        # reverse the required time now cache, queue should be equal
        dept.reverse_required_time()
        self.assertEqual(dept.cache, dept.queue)


class RestaurantTest(unittest.TestCase):

    def test_create_from_line(self):
        # test 1
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)

        self.assertEqual(rest.id, 'R1')
        self.assertEqual(len(rest.departments), 3)

    def test_check_inventory(self):

        # test1
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)
        line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
        order = Order.create_from_line(line)
        bool = rest.check_inventory(order)
        self.assertEqual(bool, True)

        # test2
        line = "R1,4C,1,3A,2,2P,1,0,200,200,100,100"
        rest = Restaurant.create_from_line(line)
        line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
        order = Order.create_from_line(line)
        bool = rest.check_inventory(order)
        self.assertEqual(bool, False)

    def test_commit_inventory(self):
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)
        self.assertNotEqual(rest.inventory, rest.cache_inventory)

        rest.cache_inventory = [100, 200, 200, 100, 99]
        rest.commit_inventory()
        self.assertListEqual(list(rest.inventory.as_array()),
                             list(rest.cache_inventory))

    def test_commit_required_time(self):
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)

        with patch.object(Department, 'commit_required_time', return_value='TESTING') as mock_method:
            rest.commit_required_time()
            mock_method.assert_called()
            self.assertEqual(3, mock_method.call_count)

    def test_reverse_required_time(self):
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)

        with patch.object(Department, 'reverse_required_time', return_value='TESTING') as mock_method:
            rest.reverse_required_time()
            mock_method.assert_called()
            self.assertEqual(3, mock_method.call_count)

    def test_required_time(self):
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)
        with patch.object(Department, 'required_time', return_value=10) as mock_method:
            line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
            order = Order.create_from_line(line)
            req_time = rest.required_time(order)
            self.assertEqual(30, req_time)
            mock_method.assert_called()
            self.assertEqual(3, mock_method.call_count)

    def test_check_order(self):
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)

        line = "R1,2020-12-08 19:15:31,O1,BLT,LT,VLT"
        order = Order.create_from_line(line)

        order = rest.check_order(order, 21*60)
        self.assertEqual('ACCEPTED', order.status)

    def test_repr(self):
        line = "R1,4C,1,3A,2,2P,1,100,200,200,100,100"
        rest = Restaurant.create_from_line(line)
        self.assertEqual(
            'R1,TOTAL,0\nR1,INVENTORY,100,200,200,100,100', str(rest))


if __name__ == "__main__":
    unittest.main()
