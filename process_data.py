from __future__ import division
import pandas as pd
import psycopg2


def database_connect(dbnm, username):
    '''
    INPUT: name of existing postgres database, username
    OUTPUT: database connection and cursor
    Take database name and username and establish conncetion to database
    '''
    conn = psycopg2.connect(dbname=dbnm, user=username, host='/tmp')
    c = conn.cursor()
    return conn, c


def remove_rows(df, colname, colval):
    '''
    INPUT: dataframe, column name, column value
    OUTPUT: dataframe
    take a dataframe and remove all rows in which the value for colname = colval
    '''
    return df[df[colname] != colval]


def remove_outliers(df, colname, iqr_mult):
    '''
    INPUT: dataframe, column name, multiplier for inter quartile range
    OUTPUT: dataframe
    take a dataframe and return a dataframe with outliers removed
    '''
    q1 = df[colname].quantile(.25)
    q3 = df[colname].quantile(.75)
    iqr = df[colname].quantile(.75) - df[colname].quantile(.25)  # calculate interquartile range
    df = df[df[colname] >= q1 - iqr * iqr_mult]  # remove low outliers
    df = df[df[colname] <= q3 + iqr * iqr_mult]  # remove high outliers
    return df


def extract_from_database(dbname, user, table, cols):
    '''
    INPUT: database name, username, table name, columns to extract
    OUTPUT: dataframe
    take a postgres database, extract specified columns from it and return as a dataframe
    '''
    conn, c = database_connect('housingdata_clean', 'sydneydecoto')
    df = pd.DataFrame()
    for col in cols:
        c.execute('SELECT {} FROM {}'.format(col, table))
        df[col] = [val[0] for val in c.fetchall()]
    conn.commit()
    conn.close()
    return df

def get_permit_count(df, hood, category):
    '''
    INPUT: dataframe, neighborhood, and construction permit category
    OUTPUT:
    '''
    return df.loc[(df['Neighborhood'] == hood) & (df['Category'] == category), 'Value'].count()

def get_permit_sum(df, hood, category):
    return df.loc[(df['Neighborhood'] == hood) & (df['Category'] == category), 'Value'].sum()


if __name__ == '__main__':
    '''Process housing data'''
    # get columns from database
    params_list = ['v2014', 'v2015', 'v2016', 'hood', 'year', 'sq_ft', 'beds', 'baths', 'lot_size']
    df = extract_from_database('housingdata_clean', 'sydneydecoto', 'housing_data', params_list)

    # add columns for percent increase from 2014 to 2015 and percent increase from 2015 to 2016 (this will be y)
    df['pct_inc15'] = (df['v2015'] - df['v2014']) / df['v2014']*100.
    df['pct_inc16'] = (df['v2016'] - df['v2015']) / df['v2015']*100.

    '''remove bad data (null values, zero home values)'''
    df.dropna(axis=0, inplace=True)
    df = remove_rows(df, 'v2014', 0)
    df = remove_rows(df, 'v2015', 0)
    df = remove_rows(df, 'v2016', 0)
    df = remove_outliers(df, 'pct_inc16', 3)
    df = remove_outliers(df, 'pct_inc15', 3)
    # df.info()

    '''Process construction permit data'''
    permits_2015 = pd.read_csv('data/permits_2015.csv')
    permits_2015['Value'] = permits_2015['Value'].replace('[$]', '', regex=True).astype(float)
