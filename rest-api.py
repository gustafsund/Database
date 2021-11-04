#This will be the REST API for the project 
#Authors: Douglas Ihre & Gustaf Sundell

from bottle import get, post, run, request, response
from urllib.parse import quote, unquote
import sqlite3

db = sqlite3.connect('project-db.sqlite') #The database for the project


@post('/reset')
def reset_db():
    c = db.cursor()

    tables = ['pallets','orders','customers','suborders','inventory','recipe_items','recipes']
    
    for table in tables:
        c.execute(
            f'DELETE FROM {table};'
        )
    
    response.status = 205
    db.commit()

    return {"location": "/"}

@post('/customers')
def post_customer():
    customer = request.json
    name = unquote(customer['name'])
    address = unquote(customer['address'])

    c = db.cursor()
    c.execute(
    """
    INSERT
    INTO    customers(customer_name, customer_address)
    VALUES  (?,?)
    """
    , [name, address])

    response.status = 201
    db.commit()
    return {"location": f'/customers/{quote(name)}'}

@get('/customers')
def get_customers():
    c = db.cursor()

    c.execute(
        """
        SELECT  customer_name, customer_address
        FROM    customers
        """
    )
    found = [{'name':customer_name, 'address': customer_address} for customer_name, customer_address in c]

    response.status = 200
    return {'data':found}


@get("/ingredients")
def get_ingredients():
    c = db.cursor()
    c.execute(
        '''
        SELECT ingredient, sum(amount) AS quantity, unit
        FROM   inventory
        GROUP BY ingredient
        '''
    ,[])
    found = []
    [found.append({'ingredient':ingredient, 
                   'quantity':quantity,
                   'unit':unit}) 
     for ingredient,quantity,unit in c]
     
    response.status = 200
    return {'data':found}

@post('/ingredients')
def post_ingredients():
    ingred=request.json
    ingredient = unquote(ingred['ingredient'])
    unit = unquote(ingred['unit'])
    c = db.cursor()
    c.execute(
        '''
        INSERT 
        INTO inventory(ingredient, unit)
        VALUES (?,?)
        ''',
        [ingredient,unit]
    )
    response.status = 201
    db.commit()
    return {'location':f'/ingredients/{quote(ingredient)}'}

@post('/ingredients/<ingredient_name>/deliveries')
def post_ingredients(ingredient_name):
    ingredient_name = unquote(ingredient_name)
    payload = request.json
    c = db.cursor()

    # Add ingredients
    c.execute("""
        INSERT INTO inventory(ingredient,amount,date)
        VALUES (?,?,?)
    """,[ingredient_name, payload['quantity'], unquote(payload['deliveryTime'])])

    db.commit()

    c = db.cursor()
    #Find quantity of ingredient in stock
    c.execute("""
        SELECT  unit, SUM(amount) AS stock
        FROM    inventory
        WHERE   ingredient = ?
    """,[ingredient_name])

    
    unt = ""
    stck = ""
    for unit, stock in c:
        unt = unit
        stck = stock
    #found = ({'unit': unit, 'quantity': stock} for unit, stock in c)

    response.status = 201

    return {'data': {'ingredient': ingredient_name, 'quantity': stck, 'unit': unt}}



@post('/cookies')
def post_cookies():
    cookie = request.json
    cookie_type = unquote(cookie['name'])

    c = db.cursor()
    #Add cookie to recipies
    c.execute(
        """
        INSERT 
        INTO    recipes(cookie_type)
        VALUES  (?)
        """
    , [cookie_type])

    #Add ingredients to recipe_items
    recipe_list = cookie['recipe']
    for item in recipe_list:
        c.execute(
            """
            INSERT
            INTO    recipe_items(cookie_type, ingredient, amount)
            VALUES  (?,?,?)
            """
        ,[cookie_type, unquote(item['ingredient']), item['amount']])

    response.status = 201
    db.commit()
    return {"location": f'/cookies/{quote(cookie_type)}'}

@get('/cookies')
def get_cookies():
    c = db.cursor()

    c.execute(
        """
        SELECT      cookie_type, coalesce(count(*),0) as cnt
        FROM        recipes
        LEFT JOIN   pallets
        USING       (cookie_type)
        GROUP BY    cookie_type
        """
    )
    found = []
    [found.append({'name':cookie_type, 'pallets': cnt}) for cookie_type, cnt in c]
    print('Get cookies: ',found)
    response.status = 200

    return {"data": found}

@get('/cookies2')
def get_cookies():
    c = db.cursor()

    c.execute(
        """
        SELECT      cookie_type
        FROM        recipes
        """
    )
    found = []
    [found.append({'name':cookie_type}) for cookie_type in c]

    response.status = 200

    return {"data": found}

@get('/cookies/<cookie_name>/recipe')
def get_specific_recipe(cookie_name):
    c = db.cursor()

    c.execute(
        """
        SELECT  ingredient, amount, unit
        FROM    recipe_items
        WHERE   cookie_type = ?
        """
    , [unquote(cookie_name)])

    found = []
    [found.append({'ingredient': ingredient, 'amount': amount, 'unit': unit}) for ingredient, amount, unit in c]

    response.status = 200 if len(found) > 0 else 404
    return {'data': found}

@post('/pallets')
def post_pallets():
    c = db.cursor()
    cookie_name = unquote(request.json['cookie'])

    try:
        c.execute(
            """
            SELECT ingredient, (amount*54) AS amount_used
            FROM recipe_items
            WHERE cookie_type = ?;
            """,[cookie_name]
        )
        recipes = [{"ingredient":ingredient_used, "amount":amount_used} 
        for ingredient_used, amount_used in c]

        for line in recipes:
            c.execute(
                """
                INSERT INTO inventory(ingredient,amount)
                VALUES (?,?)
                """,[line["ingredient"],-1*line["amount"]]
            )

        c.execute(
            """
            INSERT INTO pallets(production_time,cookie_type)
            VALUES (CURRENT_TIMESTAMP,?)
            """,[cookie_name]
        )

        c.execute(
            """
            SELECT pallet_id
            FROM pallets
            WHERE rowid = last_insert_rowid()
            """
        )
        id = c.fetchone()[0]
        db.commit()
        response.status = 201
        return {'location':'/pallet/'+id}
    except sqlite3.Error as er:
        print(er)
        response.status = 422
        db.rollback()
        return {"location": ""}


@get('/pallets')
def get_pallets():
    c = db.cursor()
    query = """
            SELECT pallet_id, cookie_type, production_time, blocked 
            FROM pallets
            WHERE blocked = FALSE
            """
    params =[]
    if request.query.cookie:
        query += "AND cookie_type = ?"
        params.append(unquote(request.query.cookie))
    if request.query.after:
        query += "AND production_time > ?"
        params.append(unqote(request.query.after))
    if request.query.before:
        query += "AND production_time < ?"
        params.apend(unquote(request.query.before))
    c.execute(query,params)
    db.commit()
    found = []
    [found.append({'id': pallet_id, 'cookie': cookie_type, 'productionDate': production_time, 
    'blocked':blocked},) for pallet_id,cookie_type,production_time,blocked in c]

    response.status = 200 if len(found) > 0 else 404
    return {'data': found}




@post('/cookies/<cookie_name>/block')
def block_cookie(cookie_name):
    c = db.cursor() # stod db.curson(), gissar stavfel ;) 

    query = """
            UPDATE  pallets
            SET     blocked = 1
            WHERE   cookie_type = ?
            """
    params = [unquote(cookie_name)]
    if request.query.before:
        query += "AND production_time < ?"
        params.append(unquote(request.query.before))
    if request.query.after:
        query += "AND production_time > ?"
        params.append(unquote(request.query.after))
    
    c.execute(query, params)
    response.status = 205
    db.commit()

@post('/cookies/<cookie_name>/unblock')
def unblock_cookie(cookie_name):
    c = db.cursor()

    c.execute(
        """
        UPDATE  pallets
        SET     blocked = 0
        WHERE   cookie_type = ?
        """
    ,[unquote(cookie_name)])
    
    response.status = 205
    db.commit()

    return ""


run(host='localhost', port=8888, debug=True, reloader=True)