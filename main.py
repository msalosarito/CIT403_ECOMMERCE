from fastapi import FastAPI, HTTPException, Header, Query, Body, Response
from fastapi.responses import HTMLResponse, FileResponse
from pymongo import MongoClient
from io import BytesIO

# MongoDB connection string
MONGO_URI = "mongodb+srv://msalosarito:<qwerTYasf1!>@cluster0.4eolclv.mongodb.net/"

# MongoDB database name
DATABASE_NAME = "ecommerce"

# Secret key
SECRET_KEY = "CIT"

app = FastAPI()

# Connect to MongoDB with SSL and CA certificate
client = MongoClient(MONGO_URI)

# MongoDB database and collections
db = client[DATABASE_NAME]
sales_collection = db["sales"]  # Collection for sales records

# Route to serve index.html
@app.get("/", response_class=HTMLResponse)
async def get_html():
    try:
        with open("index.html", "r") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to handle the report request
@app.get("/report")
async def get_report(x_secret_key: str = Query(..., alias="X-Secret-Key")):
    if x_secret_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Fetch sales report from the database
    sales_data = list(sales_collection.find({}, {"_id": 0, "product": 1}))
    if not sales_data:
        return {"message": "No sales data found"}

    # Prepare data for plotting
    product_names = [data["product"] for data in sales_data]
    # Assuming each sale record in the sales_data represents a sale of one unit
    # Count the occurrences of each product name to get quantities
    quantities = {}
    for product in product_names:
        if product in quantities:
            quantities[product] += 1
        else:
            quantities[product] = 1

    # Convert quantities to lists for plotting
    product_names = list(quantities.keys())
    product_quantities = list(quantities.values())

    # Generate a plot
    plt.figure(figsize=(10, 6))
    plt.bar(product_names, product_quantities, color='blue')
    plt.xlabel('Product Name')
    plt.ylabel('Quantity Sold')
    plt.title('Sales Report')
    plt.xticks(rotation=45, ha="right")

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    # Return the plot image as a response
    return Response(content=buf.getvalue(), media_type="image/png")





# Route to handle the buy request
@app.post("/buy")
async def buy_product(product_info: dict = Body(...), x_secret_key: str = Header(None)):
    try:
        product_name = product_info.get("product")
        if not product_name:
            raise HTTPException(status_code=422, detail="Product name missing in request")

        # Check secret key
        if x_secret_key != SECRET_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Insert the purchase record into the database
        sales_collection.insert_one({"product": product_name})
        return {"message": f"Successfully purchased {product_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
