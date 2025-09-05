from crewai import Agent, Task, Crew, Process
from crewai_tools import BaseTool
from langchain_openai import AzureChatOpenAI
import config
from search_tools import tiered_web_search

class ReligiousTextSearchTool(BaseTool):
    name: str = "Religious Text Search Tool"
    description: str = "Searches Qur'an and Hadith vectorstores for texts relevant to a query."
    quran_retriever: object
    hadith_retriever: object

    def _run(self, query: str) -> str:
        quran_results = self.quran_retriever.invoke(query)
        hadith_results = self.hadith_retriever.invoke(query)
        quran_context = "\n\n".join([doc.page_content for doc in quran_results])
        hadith_context = "\n\n".join([doc.page_content for doc in hadith_results])
        return f"QURANIC SOURCES:\n{quran_context}\n\nHADITH SOURCES:\n{hadith_context}"

class AdvancedWebSearchTool(BaseTool):
    name: str = "Advanced Web Search Tool"
    description: str = "Performs a tiered web search using Wikipedia and SearxNG for contemporary views, articles, and fatwas."

    def _run(self, query: str) -> str:
        return tiered_web_search(query)

def create_crew(quran_retriever, hadith_retriever):
    """Creates and configures the crewAI crew with agents, tasks, and tools."""
    advanced_search_tool = AdvancedWebSearchTool()
    religious_search_tool = ReligiousTextSearchTool(quran_retriever=quran_retriever, hadith_retriever=hadith_retriever)
    
    # Updated LLM Configuration
    llm = AzureChatOpenAI(
        azure_deployment=config.AZURE_CHAT_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION,
        temperature=0.7,
        # This line is the crucial fix, telling litellm to use the 'azure' provider
        model=f"azure/{config.AZURE_CHAT_DEPLOYMENT_NAME}"
    )

    researcher = Agent(role='Primary Source Researcher', goal='Find foundational texts about {topic}.', backstory='Expert in Islamic scriptures.', tools=[religious_search_tool], llm=llm, verbose=True)
    validator = Agent(role='Contemporary Validator', goal='Find contemporary views on {topic}.', backstory='Meticulous web researcher.', tools=[advanced_search_tool], llm=llm, verbose=True)
    synthesizer = Agent(role='Synthesis Agent', goal='Craft a comprehensive answer about {topic}.', backstory='Master communicator.', llm=llm, verbose=True)

    research_task = Task(description='Search for primary texts (Qur\'an and Hadith) related to the topic: {topic}.', expected_output='A compiled list of relevant verses and hadiths.', agent=researcher)
    validation_task = Task(description='Search the web for contemporary opinions and fatwas on the topic: {topic}.', expected_output='A summary of key findings from reliable online sources.', agent=validator)
    synthesis_task = Task(description='Analyze primary sources and web findings to synthesize a comprehensive answer for the user\'s query on {topic}.', expected_output='A final, curated answer.', agent=synthesizer, context=[research_task, validation_task])

    return Crew(agents=[researcher, validator, synthesizer], tasks=[research_task, validation_task, synthesis_task], process=Process.sequential, verbose=True)