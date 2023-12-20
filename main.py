from router import Router
from expert import StockPriceExpert, StockTransactionExpert, ImageGeneratorExpert
import pandas as pd
queries = [
    "what is price of MSFT",
    "Buy 100 shares of UBER",
    "Buy 10 shares of AAPL",
    "get me 5 microsoft",
    "dump my 100 SPY",
    "sell 100 SPY",
    "sell 100 SPY and buy 20 rivian",
    "how much is AAPL",
    "how much is SPY",
    "I want to buy 100 shares of UBER",
    "I want to sell 100 shares of MNST",
    "Draw a llama",
    "Draw a cat",
    "I want an image of a shark",
]
router = Router()
router.register(StockPriceExpert(), "stock_price")
router.register(StockTransactionExpert(), "stock_transaction")
router.register(ImageGeneratorExpert(), "image_generator")

results = []
for query in queries:
    print("processing:", query)

    output = router.dispatch(query)
    results.append([query, output])
    print(output)
    print('---')

df = pd.DataFrame(results, columns=['Query', 'Output'])
csv_file_path = 'results.csv'
df.to_csv(csv_file_path, index=False)