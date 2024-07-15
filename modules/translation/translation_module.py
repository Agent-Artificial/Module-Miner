import os
import io
import base64
from typing import Union, Optional
from fastapi import HTTPException
from dotenv import load_dotenv
from loguru import logger

from .data_models import TranslationRequest, MinerConfig, ModuleConfig, BaseMiner, TranslationConfig
from .translation import Translation

load_dotenv()


module_settings = ModuleConfig(
    module_path="module/translation",
    module_name="translation",
    module_endpoint="/modules/translation",
    module_url="https://translation.com/"
)

miner_settings = MinerConfig(
    module_name="translation",
    module_path="modules/translation",
    module_endpoint="/modules/translation",
    module_url="https://translation.com/",
    miner_key_dict={
        "test_miner_1": {
            "key": "5GN2dLhWa5sCB4A558Bkkh96BNdwwikPxCBJW6HQXmQf7ypR",
            "name": "test_miner_1",
            "host": "0.0.0.0",
            "port": 4269,
            "keypath": "$HOME/.commune/key/test_miner_1.json"
        }
    },
)
translator = Translation(TranslationConfig())


class TranslationMiner(BaseMiner):
    
    def __init__(
        self, 
        route: Optional[str] = "translation",
        inpath: Optional[str] = "modules/translation/in",
        outpath: Optional[str] = "modules/translation/out",
    ):
        """
        Initializes the TranslationMiner class with optional route, inpath, and outpath parameters.
        
        Parameters:
            route (Optional[str]): The route for the translation.
            inpath (Optional[str]): The input path for translation.
            outpath (Optional[str]): The output path for translation.
        """
        super().__init__(miner_settings, module_settings)
        self.add_route(route)
        
        os.makedirs(inpath, exist_ok=True)
        os.makedirs(outpath, exist_ok=True)
    
    def process(self, miner_request: TranslationRequest) -> Union[str, bytes]:
        """
        Processes the given `TranslationRequest` object and returns the translation result.

        Parameters:
            miner_request (TranslationRequest): The request object containing the input data, task string, source language, and target language.

        Returns:
            Union[str, bytes]: The translation result.

        Raises:
            HTTPException: If an error occurs during the translation process.

        """
        try:
            return translator.process(miner_request)
        except Exception as e:
            logger.error(f"Error processing translation: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing translation: {e}") from e
    
        
miner = TranslationMiner()

miner.add_route("translation")

miner.run_server("0.0.0.0", 4269)
