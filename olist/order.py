import numpy as np
import pandas as pd
from olist.data import get_data, get_matching_table
from olist.utils import haversine_distance

class Order:
    '''
        class instances will be DataFrames containing all 
        orders delivered as index and various properties of 
        these orders as columns
    '''
    def __init__(self):
        self.data = get_data()

    def get_wait_time(self, is_delivered = True):
        '''
            Returns a DataFrame with colums:
            [order_id, wait_time, expected_wait_time, delay_vs_expected, order_status]
            filtering out non-delivered orders unless specified
        '''

        # grab the information from the orders dataframe
        orders = self.data['orders'].copy()

        # filter delivered orders
        if is_delivered:
            orders = orders.query("order_status=='delivered'").copy()

        # convert datatype of timestamps to datetime
        orders.loc[:, 'order_delivered_customer_date'] = \
            pd.to_datetime(orders['order_delivered_customer_date'])
        orders.loc[:, 'order_estimated_delivery_date'] = \
            pd.to_datetime(orders['order_estimated_delivery_date'])
        orders.loc[:, 'order_purchase_timestamp'] = \
            pd.to_datetime(orders['order_purchase_timestamp'])

        # compute the difference between the estimated and the actual delivery dates
        orders.loc[:, 'delay_vs_expected'] = (orders['order_estimated_delivery_date'] -\
            orders['order_delivered_customer_date']) / np.timedelta64(1,'D')
        
        
        def handle_delay(x):
            # We only want to keep delay where wait_time is longer than expected (not the other way around)
            # This is what drives customer dissatisfaction!
            if x < 0:
                return abs(x)
            return 0

        orders.loc[:, 'delay_vs_expected'] = orders['delay_vs_expected'].apply(handle_delay)

        # compute the wait time between the purchase and the delivery dates
        orders.loc[:, 'wait_time'] = (orders['order_delivered_customer_date'] -\
            orders['order_purchase_timestamp']) / np.timedelta64(1,'D')
        
        # compute the  expected wait time between the purchase and the estimated delivery dates
        orders.loc[:, 'expected_wait_time'] = (orders['order_estimated_delivery_date'] -\
            orders['order_purchase_timestamp']) / np.timedelta64(1,'D')

        return orders[['order_id', 'wait_time', 'expected_wait_time',
                       'delay_vs_expected', 'order_status']]

    def get_review_score(self):
        """
            Returns a DataFrame with columns:
            [order_id, dim_is_five_star, dim_is_one_star, review_score]
        """

        # grab the information from the reviews dataframe
        reviews = self.data['order_reviews'].copy()

        # support function that return a one for 5 star reviews and 0 otherwise
        def dim_five_star(d):
            if d == 5:
                return 1
            return 0
        
        # support function that return a one for 1 star reviews and 0 otherwise
        def dim_one_star(d):
            if d == 1:
                return 1
            return 0

        reviews.loc[:, 'dim_is_five_star'] = reviews['review_score'].apply(dim_five_star)

        reviews.loc[:, 'dim_is_one_star'] = reviews['review_score'].apply(dim_one_star)

        return reviews[['order_id', 'dim_is_five_star',
                        'dim_is_one_star', 'review_score']]

    def get_number_products(self):
        """
            Returns a DataFrame with columns:
            [order_id, number_of_products]
        """

        # group by order_id and count the items per order
        products = self.data['order_items'].groupby('order_id',
            as_index=False).agg({'order_item_id': 'count'})
        products.columns = ['order_id', 'number_of_products']

        return products

    def get_number_sellers(self):
        """
            Returns a DataFrame with columns:
            [order_id, number_of_sellers]
        """

        # group by order_id and count the sellers per order
        sellers = self.data['order_items'].groupby('order_id')['seller_id'].nunique().reset_index()
        sellers.columns = ['order_id', 'number_of_sellers']

        return sellers

    def get_price_and_freight(self):
        """
            Returns a DataFrame with columns:
            [order_id, price, freight_value]
        """

        # group by order_id and take the sum for price and freight_value
        price_and_freight = self.data['order_items'].groupby('order_id', 
            as_index=False).agg({'price':'sum', 'freight_value': 'sum'})

        return price_and_freight

    def get_distance_seller_customer(self):
        """
            Returns a DataFrame with columns:
            [order_id, distance_seller_customer]
        """

        matching_table = get_matching_table()

        # Since one zipcode can map to multiple (lat, lng), take first one
        geo = self.data['geolocation']
        geo = geo.groupby('geolocation_zip_code_prefix', as_index=False).first()

        sellers = self.data['sellers']
        customers = self.data['customers']

        # get the geolocations for the sellers
        sellers_geo = sellers.merge(geo, how = 'left', left_on = 'seller_zip_code_prefix',
            right_on = 'geolocation_zip_code_prefix')['seller_id', 'seller_zip_code_prefix',
                                                      'seller_city', 'seller_state',
                                                      'geolocation_lat', 'geolocation_lng']
        
        # get the geolocations for the customers
        customers_geo = customers.merge(geo, how = 'left', left_on = 'customer_zip_code_prefix',
            right_on = 'geolocation_zip_code_prefix')['customer_id', 'customer_zip_code_prefix',
                                                      'customer_city', 'customer_state',
                                                      'geolocation_lat', 'geolocation_lng']

        # create new dataframe with customer and seller geolocations
        matching_geo = matching_table.merge(sellers_geo, on = 'seller_id').merge(customers_geo, on = 'customer_id',
            suffixes=('_seller','_customer'))

        # remove missing values
        matching_geo = matching_geo.dropna()

        # calculate the distance between seller and customer
        matching_geo.loc[:, 'distance_seller_customer'] = matching_geo.apply(
            lambda row: haversine_distance(
                row['geolocation_lng_seller'],
                row['geolocation_lat_seller'],
                row['geolocation_lng_customer'],
                row['geolocation_lat_customer']
            ), axis = 1
        )

        # for one order there can be several sellers so take the mean distance
        distance = matching_geo.groupby('order_id', as_index = False).agg({'distance_seller_customer', 'mean'})

        return distance

    def get_training_data(self, is_delivered=True,
                          with_distance_seller_customer=False):
        """
            Returns a clean DataFrame (without NaN), with the following
            columns: [order_id, wait_time, expected_wait_time, delay_vs_expected,
            dim_is_five_star, dim_is_one_star, review_score, number_of_products,
            number_of_sellers, price, freight_value, distance_customer_seller]
        """

        training_set =\
            self.get_wait_time(is_delivered)\
                .merge(
                self.get_review_score(), on='order_id'
               ).merge(
                self.get_number_products(), on='order_id'
               ).merge(
                self.get_number_sellers(), on='order_id'
               ).merge(
                self.get_price_and_freight(), on='order_id'
               )
        
        # Skip heavy computation of distance_seller_customer unless specified
        if with_distance_seller_customer:
            training_set = training_set.merge(
                self.get_distance_seller_customer(), on='order_id')
        
        # remove missing values
        training_set = training_set.dropna()

        return training_set

if __name__ == '__main__':
    orders = Order()
    data = orders.get_training_data()
    print(data.shape)