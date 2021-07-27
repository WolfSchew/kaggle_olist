import numpy as np
import pandas as pd
import os


def get_data():
    """
        This function returns a Python dict.
        Its keys are the descriptors of the data files: 'sellers', 'orders', 'order_items' etc...
        Its values are pandas.DataFrames loaded from  the csv files
    """

    # build path to the csv files
    csv_path = os.path.join(os.path.dirname(__file__),'..','data')

    # bulid a list of the csv file names
    file_names = []
    for file in os.listdir(csv_path):
        if file.endswith('csv'):
            file_names.append(file)

    # seperate the file descriptor for the keys
    key_names = []
    for file in file_names:
        key = file
        if file.startswith('olist_'):
            key = key.replace('olist_', '')
        if file.endswith('_dataset.csv'):
            key = key.replace('_dataset.csv', '')
        if file.endswith('.csv'):
            key = key.replace('.csv', '')
        key_names.append(key)

    # build the dict for the data read from the csv files
    data = {}
    for (key,file) in zip(key_names, file_names):
        data[key] = pd.read_csv(os.path.join(csv_path, file))

    return data


def get_matching_table():
    """
        This function returns a matching table between the foreign keys in the
        columns [ "order_id", "review_id", "customer_id", "product_id", "seller_id"]
    """
    data = get_data()
    orders = data['orders'][['customer_id', 'order_id']]
    reviews = data['order_reviews'][['order_id', 'review_id']]
    items = data['order_items'][['order_id', 'product_id','seller_id']]
    matching_table = orders.merge(reviews, on='order_id', how='outer').merge(items, on='order_id', how='outer')
        
    return matching_table

if __name__ == '__main__':
    # check the output of the get_data function
    data = get_data()
    print(data.keys())
    print(data['orders'].head())

    # check the output for the get_matching_table function
    matching_table = get_matching_table()
    print(matching_table.head())