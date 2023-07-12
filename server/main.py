"""Server side."""
from fastapi import FastAPI, Request, Response

app = FastAPI()


@app.get('/')
async def root(request: Request) -> Response:
    """
    Return Hello Message
    :Returns: Response
    """
    return Response('Ello, GuvNor')


@app.get('/createWallet')
async def create_wallet(request: Request) -> Response:
    """
    Create wallet
    :Returns: Response
    """
    return Response('CreateWallet')


@app.get('/getBalance')
async def get_balance(request: Request) -> Response:
    """
    Create wallet
    :Returns: Response
    """
    return Response('GetBalance')


@app.get('/getTransactions')
async def get_transactions(request: Request) -> Response:
    """
    Create wallet
    :Returns: Response
    """
    return Response('getTransactions')


@app.get('/sendTransaction')
async def get_transactions(request: Request) -> Response:
    """
    Send Transactions
    :Returns: Response
    """
    return Response('getTransactions')


@app.get('/*')
async def get_transactions(request: Request) -> Response:
    """
    Catch non valid urls
    :Returns: Response
    """
    return Response('getTransactions')
