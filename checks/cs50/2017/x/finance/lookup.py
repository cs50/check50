def lookup(symbol):
    if (symbol == "AAAA"):
        return {"name": "Stock A", "price": 28.00, "symbol": "AAAA"}
    elif (symbol == "BBBB"):
        return {"name": "Stock B", "price": 14.00, "symbol": "BBBB"}
    elif (symbol == "CCCC"):
        return {"name": "Stock C", "price": 2000.00, "symbol": "CCCC"}
    else:
        return None