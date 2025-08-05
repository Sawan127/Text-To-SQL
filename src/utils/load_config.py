import os
from dotenv import load_dotenv
import yaml
from pyprojroot import here
import shutil
from openai import OpenAI
from langchain_openai import ChatOpenAI


print("Environment variables are loaded:", load_dotenv())


class LoadConfig:
    def __init__(self) -> None:
        with open(here("configs/app_config.yml")) as cfg:
            app_config = yaml.load(cfg, Loader=yaml.FullLoader)

        self.load_directories(app_config=app_config)
        self.load_llm_configs(app_config=app_config)
        self.load_openai_models()

        # Un comment the code below if you want to clean up the upload csv SQL DB on every fresh run of the chatbot. (if it exists)
        # self.remove_directory(self.uploaded_files_sqldb_directory)

    def __getitem__(self, key):
        return self._config[key]

    def load_directories(self, app_config):
        self.stored_csv_xlsx_directory = here(
            app_config["directories"]["stored_csv_xlsx_directory"])
        self.sqldb_directory = str(here(
            app_config["directories"]["sqldb_directory"]))
        self.uploaded_files_sqldb_directory = str(here(
            app_config["directories"]["uploaded_files_sqldb_directory"]))
        self.stored_csv_xlsx_sqldb_directory = str(here(
            app_config["directories"]["stored_csv_xlsx_sqldb_directory"]))
        

    def load_llm_configs(self, app_config):
        self.model_name = os.getenv("MODEL")
        self.agent_llm_system_role = app_config["llm_config"]["agent_llm_system_role"]
        self.rag_llm_system_role = app_config["llm_config"]["rag_llm_system_role"]
        self.temperature = app_config["llm_config"]["temperature"]
        self.llm_config = app_config["llm_config"]
       

    def load_openai_models(self):
        base_url=os.environ["BASE_URL"]
        api_key=os.environ["API_KEY"]

        self.openai_client = OpenAI(
            base_url=base_url,
            api_key=api_key
            
        )
        self.langchain_llm = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=api_key,
            openai_api_base = base_url,
            temperature=self.temperature)
        
    def remove_directory(self, directory_path: str):
        """
        Removes the specified directory.

        Parameters:
            directory_path (str): The path of the directory to be removed.

        Raises:
            OSError: If an error occurs during the directory removal process.

        Returns:
            None
        """
        if os.path.exists(directory_path):
            try:
                shutil.rmtree(directory_path)
                print(
                    f"The directory '{directory_path}' has been successfully removed.")
            except OSError as e:
                print(f"Error: {e}")
        else:
            print(f"The directory '{directory_path}' does not exist.")