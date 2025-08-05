import os
from typing import List, Tuple
from utils.load_config import LoadConfig
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from sqlalchemy import create_engine
from langchain_community.agent_toolkits import create_sql_agent
import langchain
langchain.debug = True

APPCFG = LoadConfig()

class ChatBot:
    """
    A ChatBot class capable of responding to SQL queries in Auto-Detect mode.
    Supports debug mode for showing SQL query, raw result, and explanation.
    """

    @staticmethod
    def respond(chatbot: List, message: str, chat_type: str, app_functionality: str, debug: bool=False) -> Tuple:
        if app_functionality != "Chat":
            return "", chatbot, None

        response = None
        debug_output = ""

        # =========================
        # Select DB Path
        # =========================
        if chat_type == "Auto-Detect":
            if os.path.exists(APPCFG.stored_csv_xlsx_sqldb_directory):
                db_path = APPCFG.stored_csv_xlsx_sqldb_directory
            elif os.path.exists(APPCFG.sqldb_directory):
                db_path = APPCFG.sqldb_directory
            else:
                chatbot.append((message, "No SQL DB available. Please run `prepare_csv_xlsx_sqlitedb.py`."))
                return "", chatbot, None
        else:
            chatbot.append((message, "Auto-Detect mode is required for queries."))
            return "", chatbot, None
        
        # =========================
        # Connect to DB (Read-Only)
        # =========================
        engine = create_engine(f"sqlite:///file:{db_path}?mode=ro&uri=true")
        db = SQLDatabase(engine=engine)

        # =========================
        # Detect complexity
        # =========================
        simple_keywords = ["how many", "count", "total", "sum", "max", "min", "list", "show"]
        is_simple = any(keyword in message.lower() for keyword in simple_keywords)

        if is_simple:
            # --- Chain Mode
            execute_query = QuerySQLDataBaseTool(db=db)
            sql_prompt = PromptTemplate(
                input_variables=["input", "table_info", "top_k"],
                template=APPCFG.llm_config["sql_generation_prompt"]
            )
            write_query = create_sql_query_chain(APPCFG.langchain_llm, db, prompt=sql_prompt)
            answer_prompt = PromptTemplate.from_template(APPCFG.agent_llm_system_role)
            answer = answer_prompt | APPCFG.langchain_llm | StrOutputParser()

            # Debug mode captures query and result
            if debug:
                query_str = write_query.invoke({"question": message})
                debug_output += f"🔍 **SQL Query Generated:**\n```\n{query_str}\n```\n"
                result_str = execute_query.invoke(query_str)
                debug_output += f"📊 **SQL Result:**\n```\n{result_str}\n```\n"
                llm_answer = answer.invoke({"question": message, "query": query_str, "result": result_str})
                debug_output += f"💬 **LLM Answer:**\n{llm_answer}"
                response = debug_output
            else:
                chain = (
                    RunnablePassthrough.assign(query=write_query)
                    .assign(result=itemgetter("query") | execute_query)
                    | answer
                )
                response = chain.invoke({"question": message})
        else:
            # --- Agent Mode
            agent_executor = create_sql_agent(
                APPCFG.langchain_llm, db=db, agent_type="openai-tools", verbose=True
            )
            response_dict = agent_executor.invoke({"input": message})
            response = response_dict.get("output", str(response_dict))

        chatbot.append((message, response))
        return "", chatbot, None
