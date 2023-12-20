import json
import requests
import os
import re
from llama_cpp import Llama

detector_model = os.environ['STOCK_BOT_DETECTOR_MODEL']
# "...models/TheBloke/neural-chat-7B-v3-1-GGUF/neural-chat-7b-v3-1.Q5_K_M.gguf"
# processor_model ="/Users/serhiikuts/.cache/lm-studio/models/TheBloke/NexusRaven-V2-13B-GGUF/nexusraven-v2-13b.Q6_K.gguf"
# "/Users/serhiikuts/.cache/lm-studio/models/lcapellaro/llama-2-13b-ptbr-intention-classifier-chat-gguf/llama-2-13b-ptbr-intention-classifier-chat-q8_0.gguf"

processor_model = detector_model 
if not os.path.exists(detector_model):
    raise Exception("Detector model not found at: " + detector_model)

class Expert:
    def __init__(self):
        self.detector_query = ""
        self.process_query = ""
        pass

    def can_process(self, query):
        if self.process_query == "":
            return False

        llm = Llama(model_path=detector_model,
                    chat_format="llama-2", verbose=False,
                    max_tokens=48,
                    stop=["Q:", "\n"])
        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self.detector_query},
                {
                    "role": "user",
                    "content": "Q: " + query,
                }
            ]
        )
        print("    XX", output["choices"][0])
        result = output["choices"][0]["message"]["content"]
        result = result.split('\n')[0]
        # the model neural-chat-7B-v3-1-GGUF has troubles with short answers,
        # can output "answer is yes" just fine, but not "yes"
        can_handle = str(result).lower().find("yes") >= 0
        name = self.__class__.__name__
        print(f'Expert {name} {"can" if can_handle else "cannot"} handle query: ', query)
        return can_handle

    def process(self, query):
        name = self.__class__.__name__
        print(f"{name} is processing:", query)
        llm = Llama(model_path=processor_model,
                    chat_format="llama-2", 
                    verbose=False,
                    max_tokens=48,
                    stop=["Q:", "\n"])
        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self.process_query},
                {
                    "role": "user",
                    "content": "Q: " + query,
                }
            ]
        )
        # print("processing done:", output)
        print(output["choices"][0])
        result = output["choices"][0]["message"]["content"]
        return result


class StockPriceExpert(Expert):
    def __init__(self):
        self.detector_query = "Analyze the conversation below, Identify if the user is asking about stock pricing. Provide 'answer is yes' if user asks for price or quote otherwise reply with 'answer is no'. Example: Q: What is the price of QQQ? A: answer is yes"
        self.process_query = """you are stock assistant bot
Parse request below into JSON array format [{"ticker":"MSFT", "op":"price"}]
only output JSON array"
examples:
Q: price of AAPL
A:  [{"ticker": "AAPL",  "op":"price"}]
Q: quote for microsoft
A:  [{"ticker": "MSFT",  "op":"price"}]
Q: what is the price of SPY and QQQ
A:  [{"ticker": "SPY",  "op":"price"}, {"ticker": "QQQ",  "op":"price"}]
"""

    def can_process(self, query):
        # print("StockPriceExpert can_process call", query)
        return Expert.can_process(self, query)

    def process(self, query):
        try:
            print("StockPriceExpert process call start")
            result = Expert.process(self, query)
            print("StockPriceExpert process call", result)
            # Extract the JSON string from the result
            # TODO: train a better model that outputs JSON directly not text with JSON
            start = result.find("[{")
            end = result.rfind("}]") + 2
            json_string = result[start:end]

            # Parse the JSON string
            print("json_string", json_string)
            data = json.loads(json_string)
            ticker = data[0]["ticker"] # TODO: handle multiple tickers
            price = self.get_stock_price(ticker)
            return f"Price of {ticker} is {price}"
        except Exception as e:
            return str(e)

    def get_stock_price(self, symbol):
        """get a stock price from alpha vantage"""

        url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=" + \
            symbol + "&apikey=" + os.environ['ALPHA_VANTAGE_API_KEY']
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)

        data = json.loads(response.text)
        # format current date as 2023-12-15
        today = data['Meta Data']['3. Last Refreshed']
        return data['Time Series (Daily)'][today]['1. open']


class StockTransactionExpert(Expert):
    def __init__(self):
        self.detector_query = """Analyze the conversation below, Identify if the user wants to make a stock transaction. 
Provide 'answer is yes' if user asks to buy or sell some stock otherwise reply with 'answer is no'. 
Examples: 
Q: Buy 100 shares of MSFT A: answer is yes
Q: get me 5 microsoft A: answer is yes
Q: sell my 100 USO A: answer is yes
        """
        self.process_query = """you are stock assistant bot
Parse request below into JSON array format [{ticker, quantity, op}]
only output JSON array
examples:
Q: Buy 10 AAPL
A:  [{"ticker": "AAPL",  "op":"buy" , "quantity":10}]  
Q: get me 5 microsoft
A:  [{"ticker": "MSFT",  "op":"buy" , "quantity":5}]  
Q: dump my 100 SPY
A:  [{"ticker": "SPY",  "op":"sell" , "quantity":10}]
Q: sell 100 SPY and buy 20 rivian
A:  [{"ticker": "SPY",  "op":"sell" , "quantity":100}, {"ticker": "RIVN",  "op":"buy" , "quantity":20}] 
"""

    def can_process(self, query):
        print("StockTransactionExpert can_process call", query)
        return Expert.can_process(self, query)

    def process(self, query):
        try:
            print("StockTransactionExpert process call", query)
            result = Expert.process(self, query)
            start = result.find("[{")
            end = result.rfind("}]") + 2
            json_string = result[start:end]

            # Parse the JSON string
            print("json_string", json_string)
            data = json.loads(json_string)
            return data
        except Exception as e:
            print("Error occurred:", str(e))
            return None


class ImageGeneratorExpert(Expert):
    def __init__(self):
        self.detector_query = """Analyze the conversation below, Identify if the user wants to generate an image.
Provide 'answer is yes' if user asks to buy or sell some stock otherwise reply with 'answer is no'. 
Examples: 
Q: Draw a cat A: answer is yes
Q: I want an image of a shark A: answer is yes
"""
        self.process_query = """extract what to generate from the query and return the image link http://example.com/{name}.png
examples:
Q: generate a cat
A: http://example.com/cat.png
Q: draw a dog
A: http://example.com/dog.png"""
    def can_process(self, query):
        print("StockTransactionExpert can_process call", query)
        return Expert.can_process(self, query)

    def process(self, query):
        try:
            print("ImageGeneratorExpert process call", query)
            result = Expert.process(self, query)
            # regex filter for all instances http://example.com/....png

            regex = r"(http:\/\/example\.com\/.*\.png)"
            matches = re.findall(regex, result)
            return " ".join(matches)
        except Exception as e:
            print("Error occurred:", str(e))
            return None