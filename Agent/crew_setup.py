from crewai import Agent, Task, Crew, Process
from crewai_tools import BaseTool, SerperDevTool
from langchain_openai import AzureChatOpenAI
import config

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

def create_crew(quran_retriever, hadith_retriever):
    """Creates and configures the crewAI crew with agents, tasks, and tools."""
    religious_search_tool = ReligiousTextSearchTool(quran_retriever=quran_retriever, hadith_retriever=hadith_retriever)
    serper_tool = SerperDevTool()
    llm = AzureChatOpenAI(
        azure_deployment=config.AZURE_CHAT_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION,
        temperature=0.7
    )

    researcher = Agent(
        role='Primary Source Researcher',
        goal='Find foundational texts from the Qur\'an and Hadith relevant to the user\'s query on {topic}.',
        backstory='An expert in Islamic scriptures, skilled at navigating vast digital libraries to find relevant passages.',
        tools=[religious_search_tool], llm=llm, verbose=True
    )
    validator = Agent(
        role='Contemporary Validator',
        goal='Find contemporary views, news, and fatwas on {topic} from trusted online sources.',
        backstory='A meticulous researcher who cross-references findings with modern-day scholarly opinions available on the web.',
        tools=[serper_tool], llm=llm, verbose=True
    )
    synthesizer = Agent(
        role='Synthesis Agent',
        goal='Craft a comprehensive, balanced, and well-structured answer to the user\'s query on {topic}.',
        backstory='A master communicator skilled at synthesizing complex information into a clear and nuanced response.',
        llm=llm, verbose=True
    )

    research_task = Task(description='Search for primary texts (Qur\'an and Hadith) related to the topic: {topic}.', expected_output='A compiled list of relevant verses and hadiths, with full text.', agent=researcher)
    validation_task = Task(description='Search the web for contemporary opinions and fatwas on the topic: {topic}.', expected_output='A summary of key findings from diverse online sources.', agent=validator)
    synthesis_task = Task(description='Analyze primary sources and web findings to synthesize a comprehensive answer for the user\'s query on {topic}.', expected_output='A final, curated answer ready to be presented to the user.', agent=synthesizer, context=[research_task, validation_task])

    return Crew(agents=[researcher, validator, synthesizer], tasks=[research_task, validation_task, synthesis_task], process=Process.sequential, verbose=True)