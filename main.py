from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from ariadne import gql, make_executable_schema, QueryType, graphql_sync
from ariadne.asgi import GraphQL
from typing import List, Optional

# Simulate JSON data fetched from Snowflake
json_data = [
    {
        "customerID": "900",
        "firstname": "John",
        "lastname": "Smith",
        "accounts": [
            {
                "accountnumber": "777",
                "paymentstatus": "Paid",
                "address": [
                    {"addline1": "201 Dr", "city": "Frisco"},
                    {"addline1": "202 Dr", "city": "Dallas"}
                ]
            },
            {
                "accountnumber": "778",
                "paymentstatus": "Due",
                "address": [
                    {"addline1": "203 Dr", "city": "Plano"}
                ]
            }
        ]
    },
    {
        "customerID": "901",
        "firstname": "Jane",
        "lastname": "Doe",
        "accounts": [
            {
                "accountnumber": "779",
                "paymentstatus": "Paid",
                "address": [
                    {"addline1": "204 Dr", "city": "Austin"}
                ]
            }
        ]
    }
]

# Define the GraphQL schema
type_defs = gql("""
    type Address {
        addline1: String
        city: String
    }

    type Account {
        accountnumber: String
        paymentstatus: String
        address: [Address]
    }

    type Customer {
        customerID: String
        firstname: String
        lastname: String
        accounts: [Account]
    }

    type Query {
        customer(customerID: String!): Customer
        account(accountnumber: String!): Account
    }
""")

# Define query resolvers
query = QueryType()

@query.field("customer")
def resolve_customer(_, info, customerID):
    for customer in json_data:
        if customer["customerID"] == customerID:
            return customer
    return None

@query.field("account")
def resolve_account(_, info, accountnumber):
    for customer in json_data:
        for account in customer["accounts"]:
            if account["accountnumber"] == accountnumber:
                return {
                    "accountnumber": account["accountnumber"],
                    "paymentstatus": account["paymentstatus"],
                    "address": account["address"]
                }
    return None

# Create executable schema
schema = make_executable_schema(type_defs, query)

# Initialize FastAPI app
app = FastAPI()

# Mount GraphQL endpoint
app.add_route("/graphql", GraphQL(schema, debug=True))



# REST endpoint to query via GraphQL using accountnumber
@app.get("/graphql-query")
def graphql_query(accountnumber: str):
    query = """
    query getAccount($accountnumber: String!) {
        account(accountnumber: $accountnumber) {
            accountnumber
            paymentstatus
            address {
                addline1
                city
            }
        }
    }
    """
    # Execute the GraphQL query
    variables = {"accountnumber": accountnumber}
    success, result = graphql_sync(schema, {"query": query, "variables": variables})

    if not success or not result.get("data", {}).get("account"):
        raise HTTPException(status_code=404, detail="Account not found")

    return result["data"]["account"]

# Pydantic models for REST API responses
class AddressModel(BaseModel):
    addline1: str
    city: str

class AccountModel(BaseModel):
    accountnumber: str
    paymentstatus: str
    address: List[AddressModel]

class CustomerModel(BaseModel):
    customerID: str
    firstname: str
    lastname: str
    accounts: List[AccountModel]
# REST endpoint to fetch customer data by customerID
@app.get("/customer", response_model=Optional[CustomerModel])
def get_customer(customerID: str):
    for customer in json_data:
        if customer["customerID"] == customerID:
            return customer
    raise HTTPException(status_code=404, detail="Customer not found")
# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI with GraphQL and JSON Example. Visit /docs for REST API docs and /graphql for GraphQL Playground."}
