import cx_Oracle

import csv
import datetime

class connections():

    con = ''
    cur = ''

    def __init__(self,dtls):
            connections.con = cx_Oracle.connect(dtls)
            connections.cur = connections.con.cursor()
            connections.cur.execute("select Table_name from user_tables where table_name = 'PRODUCT'")
            table = connections.cur.fetchone()
            if table is None :
                with open('script.sql', 'r') as sqlfile:
                    f = sqlfile.read()
                    flist = f.split(';')
                for query in flist:
                    connections.cur.execute(query)
                print("Database Objects Created")

class SuperMarket(connections):

    list_items = {}

    sql = """ merge into product x using (select upper(:1) as pt, :2 as pq, :3 as pp, :4 as dt from dual) y on (x.ProductName = y.pt)
              when MATCHED then
              update set x.productquantity = x.productquantity + y.pq, x.productprice = y.pp, x.updatedate = y.dt where x.productname = y.pt
              when NOT MATCHED then
              insert (x.productname,x.productquantity,x.productprice,x.updatedate) values (y.pt, y.pq, y.pp, y.dt)"""

    sql_hist = """ insert into product_hist values (:1,:2,:3,:4,:5,:6,:7) """

    sql_1 = """ select ProductName,ProductQuantity,ProductPrice from product where ProductName = :1 """

    def ItemEntry(self, **items):
        self.items = items
        slist = []
        slist_h = []
        for i,v in self.items.items():
            slist.append((i,self.items[i][0],self.items[i][1],datetime.datetime.now()))
            connections.cur.execute(SuperMarket.sql_1,[i.upper()])
            rst = connections.cur.fetchone()
            if rst is None:
                pq,pp = None,None
            else:
                pt,pq,pp = rst
            slist_h.append((i.upper(),self.items[i][0],self.items[i][1],'A',pq,pp,datetime.datetime.now()))

        connections.cur.executemany(SuperMarket.sql,slist)
        connections.cur.executemany(SuperMarket.sql_hist,slist_h)
        connections.con.commit()
        print('Items Stored in Warehouse')
        print('-' * 70)

    def itemtosold(self, **itemsold):
        self.itemsold = itemsold
        self.totalbill = 0

        alist = []
        blist = []
        clist = []
        print('Items       Quantity               Price')
        print('-' * 70)
        for k,vl in self.itemsold.items():
            Price, Remquantity = 0, 0
            connections.cur.prepare('select ProductName,ProductQuantity,ProductPrice from product where ProductName = :PN')
            connections.cur.execute(None,{'PN':k.upper()})
            Pqp = connections.cur.fetchone()
            if Pqp is None:
                blist.append(k)
            else:
                Pdt,Pdq,Pdp = Pqp
                if (Pdq > 0):
                    if vl <= Pdq:
                        Price = Pdp * vl
                        print(f'{k:10}{vl:10}{Price:20}')
                        Remquantity = Pdq - vl
                        connections.cur.execute('update product set ProductQuantity = :1 where ProductName = :2',[Remquantity,k.upper()])
                        connections.con.commit()
                        self.totalbill = self.totalbill + Price
                    else:
                        alist.append(k)
                else:
                    clist.append(k)

        print('-' * 70)
        print('Total Bill = {}'.format(self.totalbill))

        n = 0
        for r in alist:
            if n == 0:
                print('-' * 70)
                print('Items       Quantity               Remarks')
            n = n + 1
            connections.cur.prepare('select ProductQuantity from product where ProductName = :PN')
            connections.cur.execute(None,{'PN':r.upper()})
            ped = connections.cur.fetchone()
            for i in ped:
                y = i
            print(f'{r:10}{y:10}               Quantity less than expected')

        n = 0
        for x in blist:
            if n == 0:
                print('-' * 70)
                print('Items                              Remarks')
            n = n + 1
            print(f'{x:35}Not Registered')

        n = 0
        for y in clist:
            if n == 0:
                print('-' * 70)
                print('Items                              Remarks')
            n = n + 1
            print(f'{y:35}Out of Stock')

    @staticmethod
    #To Check for availabe items.
    def itemsavailable (item):
        connections.cur.prepare('select ProductQuantity,ProductPrice from product where ProductName = :PN')
        connections.cur.execute(None,{'PN':item.upper()})
        ia = connections.cur.fetchone()
        if ia is None:
            print(f'{item} - Not Registered')
        else:
            pq,pp = ia
            if pq > 0:
                print (f'{item} are available with quantity {pq} and price {pp}')
            else:
                print(f'{item} - Out of stock')

    @staticmethod
    #To delete and edit quantity,prive of availabe items.
    def editavailableitems(item,mode1,mode2 = None):
        connections.cur.execute(SuperMarket.sql_1,[item.upper()])
        ia = connections.cur.fetchone()
        if ia is None:
            print(f'{item} - Not Registered')
        else:
            pt,pq,pp = ia
            if mode1.upper() == 'D':
                pqd,ppd = None,None
                connections.cur.execute('delete from product where ProductName = :1',[item.upper()])
                connections.cur.execute(SuperMarket.sql_hist,[item.upper(),pqd,ppd,'D',pq,pp,datetime.datetime.now()])
                print(f'{item} deregistered from system')
            elif mode1.upper() == 'Q':
                connections.cur.execute('update product set ProductQuantity = :1,updatedate = :2 where ProductName = :3',[mode2,datetime.datetime.now(),item.upper()])
                connections.cur.execute(SuperMarket.sql_hist,[item.upper(),mode2,pp,'UQ',pq,pp,datetime.datetime.now()])
                print(f'{item} updated with quantity {mode2}')
            elif mode1.upper() == 'P':
                connections.cur.execute('update product set ProductPrice = :1,updatedate = :2 where ProductName = :3',[mode2,datetime.datetime.now(),item.upper()])
                connections.cur.execute(SuperMarket.sql_hist,[item.upper(),pq,mode2,'UP',pq,pp,datetime.datetime.now()])
                print(f'{item} price changed to {mode2}')
            else:
                print('Invalid Field')
            connections.con.commit()

    @staticmethod
    def itemsentryfiles(FileName):
        file_list = []
        with open(FileName,'r') as cr:
            file_read = csv.reader(cr, delimiter = ',')
            next(file_read)
            for i in file_read:
                file_list.append((i[0],i[1],i[2],datetime.datetime.now()))

        connections.cur.executemany(SuperMarket.sql,file_list)
        connections.con.commit()


sm = SuperMarket('hr/kunal@localhost/orcl')

#class ChildSuperMarket(SuperMarket,connections):
    #pass





#sp = SuperMarket(Sugar = [100,50], Apple = [0,10], Banana = [100, 8], Salt = [50, 12], Paneer = [20, 75])
#sp = SuperMarket(Sugar = [100,40])
#sp.itemtosold(Sugar = 1)
#sp.itemtosold(Sugar = 1,Apple = 50,Salt = 2,Paneer = 25,Daliya = 1)

#sp.noofitems('Lasun')
#print(sp.list_items)
#csp = ChildSuperMarket()
#csp.itemtosold(Sugar = 1,Apple = 50,Salt = 2,Paneer = 25,Daliya = 1,banana = 15)

#csp.itemsavailable('apple')
#csp.editavailableitems('Apple','D')
