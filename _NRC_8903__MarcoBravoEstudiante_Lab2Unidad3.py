# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 23:21:54 2022

@author: Marco Bravo 
"""

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from datetime import datetime
import psycopg2

def log(logfile, message):
    timestamp_format = '%H:%M:%S-%h-%d-%Y'
    #Hour-Minute-Second-MonthName-Day-Year
    now = datetime.now() # get current timestamp
    timestamp = now.strftime(timestamp_format)
    with open(logfile,"a") as f: 
        f.write('[' + timestamp + ']: ' + message + '\n')
        print(message)

def transform():

    log(logfile, "-------------------------------------------------------------")
    log(logfile, "Inicia Fase De Transformacion")
    df_fact_sales = pd.read_sql_query("""
      SELECT invoice_items.InvoiceLineId as FactId,
      invoices.InvoiceId, customers.CustomerId, 
      customers.SupportRepId as EmployeeId, 
      invoice_items.TrackId, 
      artists.ArtistId,customers.CustomerId as LocationId, 
      strftime('%Y%m%d', datetime(invoices.InvoiceDate)) as TimeId, 
      invoice_items.UnitPrice*invoice_items.Quantity as Price 
      FROM invoice_items 
        INNER JOIN invoices  ON invoices.InvoiceId = invoice_items.InvoiceId
        INNER JOIN customers  ON customers.CustomerId = invoices.CustomerId
        INNER JOIN tracks  ON tracks.TrackId = invoice_items.TrackId
        INNER JOIN albums  ON albums.AlbumId = tracks.AlbumId
        INNER JOIN artists  ON artists.ArtistId = albums.ArtistId
        ORDER BY 1;
        """, con=engine.connect())

    df_customers = pd.read_sql_query("""
        SELECT 
        CustomerId, 
        FirstName, 
        LastName, 
        CASE
           WHEN Company is NOT NULL then Company
        ELSE 'NA'
        END
        Company,
        Address, 
        City, 
        CASE
           WHEN State is NOT NULL then State
        ELSE 'NA'
        END
        State,
        Country, 
       CASE
          WHEN PostalCode is NOT NULL then PostalCode 
       ELSE 'NA'
       END
       PostalCode,
        CASE
           WHEN Phone is NOT NULL then Phone
        ELSE 'NA'
        END
        Phone,
        CASE
           WHEN Fax is NOT NULL then Fax
        ELSE 'NA'
        END
        Fax,
        Email 
        FROM customers;
        """, con=engine.connect())
    df_employees = pd.read_sql_query("""SELECT 
        EmployeeId, 
        LastName, 
        FirstName, 
        Title, 
        BirthDate, 
        HireDate, 
        Address, 
        City, 
        State, 
        Country, 
        PostalCode, 
        Phone, 
        Fax, 
        Email 
        FROM employees;
        """, con=engine.connect())
    df_location = pd.read_sql_query("""SELECT 
        CustomerId as LocationId, 
        Address, 
        City, 
        CASE
           WHEN State is NOT NULL then State
        ELSE 'NA'
        END
        State,
        Country, 
        CASE
           WHEN PostalCode is NOT NULL then PostalCode 
        ELSE 'NA'
        END
        PostalCode 
        FROM customers;
        """, con=engine.connect())
    df_tracks = pd.read_sql_query("""
        SELECT tracks.TrackId, 
        tracks.Name as TrackName,
        albums.Title as Album, 
        genres.Name as Genre, 
        media_types.Name as MediaType, 
        CASE
           WHEN tracks.Composer is NOT NULL then tracks.Composer
        ELSE 'NA'
        END
        Composer,
        tracks.Milliseconds,
        tracks.Bytes, tracks.UnitPrice as Price 
        FROM tracks 
        JOIN albums on tracks.AlbumId = albums.AlbumId
        JOIN genres  on tracks.GenreId = genres.GenreId
        JOIN media_types  on media_types.MediaTypeId = tracks.MediaTypeId
        ORDER BY 1;
        """, con=engine.connect())
    df_artists = pd.read_sql_query("""SELECT ArtistId, Name as ArtistName FROM artists ;""", con=engine.connect())

    log(logfile, "Finaliza Fase De Transformacion")
    log(logfile, "-------------------------------------------------------------")
    return df_fact_sales,df_customers,df_employees,df_location,df_tracks,df_artists
   
def load():
    """ Connect to the PostgreSQL database server """
    conn_string = 'postgresql://postgres:172164@localhost/DW_sales_music'
    db = create_engine(conn_string)
    conn = db.connect()
    try:
        log(logfile, "-------------------------------------------------------------")
        log(logfile, "Inicia  Carga")
        df_customers.to_sql('dim_customers', conn, if_exists='append',index=False)
        df_employees.to_sql('dim_employees', conn, if_exists='append',index=False)
        df_location.to_sql('dim_location', conn, if_exists='append',index=False)
        df_tracks.to_sql('dim_tracks', conn, if_exists='append',index=False)
        df_artists.to_sql('dim_artists', conn, if_exists='append',index=False)
        df_fact_sales.to_sql('fact_sales', conn, if_exists='append',index=False)
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        log(logfile, "Finaliza Carga")
        log(logfile, "-------------------------------------------------------------")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally: 
        if conn is not None:
            conn.close()
            print('Conexion de la base de datos cerrada.')

def extract():
    log(logfile, "--------------------------------------------------------")
    log(logfile, "Inicia Extraccion")
    metadata = MetaData()
    metadata.create_all(engine)
    log(logfile, "Finaliza Extraccion")
    log(logfile, "--------------------------------------------------------")


if __name__ == '__main__':
    
    logfile = "ProyectoETL_logfile.txt"
    log(logfile, "ETL iniciado.")
    engine = create_engine('sqlite:///chinook.db')
    extract()
    (df_fact_sales,df_customers,df_employees,df_location,df_tracks,df_artists) = transform()
    load()
    log(logfile, "ETL  finalizado.")
