import sqlite3




con = sqlite3.connect("inventory_project\Inventory.db")




cur = con.cursor()




cur.execute('''CREATE TABLE IF NOT EXISTS Supply
           (name text PRIMARY KEY, price real, quantity INTEGER, location text) ''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Dog Food One','48.34', '24', 'A12')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Dog Treat','8.99', '50', 'B10')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Fish Food','10.00', '10', 'J5')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Dog Toy','21.56', '75', 'B15')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Cat Food','43.89', '40', 'C5')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Cat Toy','14.99', '5', 'C10')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Dog Bed','29.95', '25', 'B20')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Cat Litter','13.00', '30', 'J15')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Flea Medicine','18.63', '6', 'E10')''')




cur.execute('''INSERT OR IGNORE INTO Supply VALUES
            ('Gold Fish','4.98', '0', 'J10')''')








con.commit()




for row in cur.execute('''SELECT * FROM Supply'''):
    print(row)
