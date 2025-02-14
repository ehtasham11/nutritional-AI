from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.text_splitter import CharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph # type
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import  HumanMessage, SystemMessage
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import List, Optional
import os
from fastapi import FastAPI, HTTPException
import uvicorn

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Setup the RAG model and FAISS VectorStore
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

try:
    loader = TextLoader("nutritionists.txt")
    index_creator = VectorstoreIndexCreator(
        embedding=embedding, 
        vectorstore_cls=FAISS,
        text_splitter=text_splitter
    )
    index = index_creator.from_loaders([loader])
except Exception as e:
    print("Error while loading or indexing the document:", e)
    index = None  # Set to None if there's an issue

# Define the RAG query tool for nutritionist data
def rag_query_tool(user_input: str) -> str:
    """
    Query the RAG model to retrieve nutritionist information.

    Args:
        user_input: The query string from the user.

    Returns:
        A string response with nutritionist details or an error message.
    """
    if not index:
        return "Nutritionist data index is not available."
    try:
        response = index.query(user_input, llm=llm)

        if response:
            # Assuming response is structured, return it formatted.
            return response
        else:
            return "No relevant nutritionist information found for your query."
    except Exception as e:
        return f"Error while querying nutritionist data: {e}"


# Define the database model for appointments
class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor: str
    date: str
    time: str
    specialization: str

# Create a SQLite database
engine = create_engine(os.getenv('DB_URI'))
SQLModel.metadata.create_all(engine)

# Correcting the book_appointment function
def book_appointment(doctor: str, date: str, time: str, specialization: str) -> str:
    """Books an appointment and saves it in the database.
    
    Args:
        doctor: The name of the doctor with whom the appointment is booked.
        specialization: The specialization of the doctor.
        date: The date of the appointment (YYYY-MM-DD).
        time: The time of the appointment (HH:MM).
    
    Returns:
        Confirmation message with appointment details.
    """
    try:
        # Use correct field names
        appointment = Appointment(doctor=doctor, date=date, time=time, specialization=specialization)
        with Session(engine) as session:
            session.add(appointment)
            session.commit()
        return f"Appointment booked successfully with Dr. {doctor} (Specialization: {specialization}) on {date} at {time}."
    except Exception as e:
        return f"Failed to book appointment: {str(e)}"


# Function to delete a booked appointment
def delete_appointment(appointment_id: int) -> str:
    """
    Deletes an appointment from the database by ID.
    
    Args:
        appointment_id: The ID of the appointment to delete.
    
    Returns:
        Confirmation message on successful deletion or an error message.
    """
    try:
        with Session(engine) as session:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return f"Appointment with ID {appointment_id} not found."
            
            session.delete(appointment)
            session.commit()
        return f"Appointment with ID {appointment_id} has been successfully deleted."
    except Exception as e:
        return f"Failed to delete appointment: {str(e)}"


search = TavilySearchResults(tavily_api_key=os.getenv("TAVILY_API_KEY"))

loader1 = WebBaseLoader("https://www.healthline.com/nutrition/1500-calorie-diet#foods-to-eat")
# loader2 = WebBaseLoader("https://www.msdmanuals.com/home")
# loader3 = WebBaseLoader("https://www.eatingwell.com/category/4305/weight-loss-meal-plans/")
docs1 = loader1.load()
# docs2 = loader2.load()
# docs3 = loader3.load()
# combined_docs = docs1 + docs2 + docs3
documents = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200
).split_documents(docs1)
vector = FAISS.from_documents(documents, GoogleGenerativeAIEmbeddings(model="models/embedding-001"))

retriever = vector.as_retriever()
retriever_tool = create_retriever_tool(
    retriever,
    "healthline_search",
    "Search for information about healthline, food, diet and nutrition. For any questions about food and nutrition, healthy diet related and just answer the question, don't explain much, you must use this tool!",
)

def calorie_calculator_tool(gender: str, weight: float, height: float, age: int, activity_level: str) -> dict:
    """
    Tool to compute daily caloric needs based on user input using the Harris-Benedict Equation.
    
    Args:
        sex (str): The user's gender ('male' or 'female').
        weight (float): The user's weight in kilograms.
        height (float): The user's height in centimeters.
        age (int): The user's age in years.
        activity_level (str): The user's activity level ('sedentary', 'light', 'moderate', 'active', 'very_active').
    
    Returns:
        dict: A dictionary containing:
            - 'bmr': Basal Metabolic Rate (calories burned at rest).
            - 'daily_calories': Estimated daily caloric needs based on activity level.
            - 'maintenance_plan': A guide for maintaining current weight.
    """
    def calculate_daily_calories(gender, weight, height, age, activity_level):
        # Basal Metabolic Rate (BMR) calculation
        if gender.lower() == "male":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        elif gender.lower() == "female":
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        else:
            raise ValueError("Invalid sex. Please use 'male' or 'female'.")

        # Activity multipliers
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        if activity_level not in activity_multipliers:
            raise ValueError("Invalid activity level. Choose from 'sedentary', 'light', 'moderate', 'active', or 'very_active'.")

        # Calculate daily caloric needs
        daily_calories = bmr * activity_multipliers[activity_level]

        base_calories = daily_calories  # Initialize with the calculated calories

        if gender == "female":
            if activity_level == "lightly":
                if 2 <= age <= 6:
                    base_calories = min(max(1000, daily_calories), 1400)
                elif 7 <= age <= 18:
                    base_calories = min(max(1200, daily_calories), 1800)
                elif 19 <= age <= 60:
                    base_calories = min(max(1600, daily_calories), 2000)
                elif age >= 61:
                    base_calories = max(1600, daily_calories)
            elif activity_level == "active":
                if 2 <= age <= 6:
                    base_calories = min(max(1000, daily_calories), 1600)
                elif 7 <= age <= 18:
                    base_calories = min(max(1600, daily_calories), 2400)
                elif 19 <= age <= 60:
                    base_calories = min(max(1800, daily_calories), 2400)
                elif age >= 61:
                    base_calories = min(max(1800, daily_calories), 2000)

        elif gender == "male":
            if activity_level == "lightly":
                if 2 <= age <= 6:
                    base_calories = min(max(1000, daily_calories), 1400)
                elif 7 <= age <= 18:
                    base_calories = min(max(1400, daily_calories), 2400)
                elif 19 <= age <= 60:
                    base_calories = min(max(2200, daily_calories), 2600)
                elif age >= 61:
                    base_calories = max(2000, daily_calories)
            elif activity_level == "active":
                if 2 <= age <= 6:
                    base_calories = min(max(1000, daily_calories), 1800)
                elif 7 <= age <= 18:
                    base_calories = min(max(1600, daily_calories), 3200)
                elif 19 <= age <= 60:
                    base_calories = min(max(2400, daily_calories), 3000)
                elif age >= 61:
                    base_calories = min(max(2200, daily_calories), 2600)

        # Determine if the user needs to gain, lose, or maintain weight
        if daily_calories < base_calories:
            weight_goal = "You should increase your calorie intake to gain weight."
        elif daily_calories > base_calories:
            weight_goal = "You should decrease your calorie intake to lose weight."
        else:
            weight_goal = "Your calorie intake is appropriate for maintaining your current weight."

        # Define diet plans
        diet_plans = {
            "1500": {
                "goal": "Weight Loss",
                "plan": [
                    "Breakfast: Greek yogurt with berries and chia seeds or oatmeal with sliced banana",
                    "Morning Snack: Apple with almond butter or a handful of mixed nuts",
                    "Lunch: Grilled chicken salad with greens and vinaigrette or quinoa salad with chickpeas and cucumber",
                    "Afternoon Snack: Cottage cheese with cucumber or carrot sticks with hummus",
                    "Dinner: Baked salmon, asparagus, and quinoa or stir-fried tofu with broccoli and brown rice",
                    "Evening Snack: Almonds or a small piece of dark chocolate"
                ]
            },
            "1800": {
                "goal": "Weight Maintenance",
                "plan": [
                    "Breakfast: Scrambled eggs with spinach, whole-grain toast or smoothie with spinach and protein powder",
                    "Morning Snack: Orange and walnuts or Greek yogurt with honey",
                    "Lunch: Turkey wrap with hummus and veggies or lentil soup with whole-grain bread",
                    "Afternoon Snack: Banana with peanut butter or rice cakes with avocado",
                    "Dinner: Grilled chicken, sweet potato, and broccoli or baked tilapia with quinoa and green beans",
                    "Evening Snack: Cottage cheese with berries or air-popped popcorn"
                ]
            },
            "2000": {
                "goal": "Moderate Weight Gain",
                "plan": [
                    "Breakfast: Overnight oats with banana and peanut butter or avocado toast with eggs",
                    "Morning Snack: Smoothie with protein powder or a protein bar",
                    "Lunch: Brown rice bowl with black beans and salsa or chicken stir-fry with vegetables",
                    "Afternoon Snack: Toast with cottage cheese and tomatoes or fruit salad",
                    "Dinner: Steak, mashed potatoes, and green beans or chicken curry with brown rice",
                    "Evening Snack: Greek yogurt with honey and pumpkin seeds or protein shake"
                ]
            },
            "2200": {
                "goal": "Active Weight Maintenance/Gain",
                "plan": [
                    "Breakfast: Omelet with veggies and whole-grain toast or smoothie bowl with fruits and granola",
                    "Morning Snack: Greek yogurt with granola and blueberries or nut butter on whole-grain bread",
                    "Lunch: Tuna wrap with veggies or quinoa salad with chickpeas and feta",
                    "Afternoon Snack: Apple and almonds or veggie sticks with hummus",
                    "Dinner: Roasted chicken, brown rice, and carrots or fish tacos with cabbage slaw",
                    "Evening Snack: Dark chocolate with walnuts or a handful of dried fruit"
                ]
            },
            "2500": {
                "goal": "High-Calorie for Weight Gain",
                "plan": [
                    "Breakfast: Smoothie bowl with peanut butter and granola or pancakes with maple syrup",
                    "Morning Snack: Crackers with cheese and apple or energy bites with oats and honey",
                    "Lunch: Quinoa bowl with chickpeas and roasted veggies or burrito with beans and cheese",
                    "Afternoon Snack: Protein bar or mixed nuts and dried fruit or yogurt with granola",
                    "Dinner: Pasta with ground turkey and salad or lamb kebabs with rice and grilled vegetables",
                    "Evening Snack: Cottage cheese with honey and mango or fruit and nut mix"
                ]
            }
        }

        # Select the appropriate diet plan based on the calculated calories
        if daily_calories <= 1500:
            selected_diet_plan = diet_plans["1500"]
        elif daily_calories <= 1800:
            selected_diet_plan = diet_plans["1800"]
        elif daily_calories <= 2000:
            selected_diet_plan = diet_plans["2000"]
        elif daily_calories <= 2200:
            selected_diet_plan = diet_plans["2200"]
        else:
            selected_diet_plan = diet_plans["2500"]
        
        # Create a maintenance plan
        maintenance_plan = {
            "maintain": round(daily_calories),
            "gain_weight": round(daily_calories + 500),
            "lose_weight": round(daily_calories - 500)
        }
        
        return {
            "bmr": round(bmr, 2),
            "daily_calories": round(daily_calories, 2),
            "maintenance_plan": maintenance_plan,
            "weight_goal": weight_goal,
            "selected_diet_plan": selected_diet_plan
        }

    # Return calculated daily calories
    return calculate_daily_calories(gender, weight, height, age, activity_level)


tools = [search, retriever_tool, calorie_calculator_tool, get_appointments, book_appointment, rag_query_tool, delete_appointment]


llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content='''You are a helpful customer support assistant specializing in calorie calculation, personalized diet plans, and health-related services. 
Your key responsibilities include calculating users' daily calorie intake, providing tailored diet plans, and assisting with appointment bookings for nutritionists.

### **Calorie Calculation Assistant**:
- Gather the following information from the user for calorie calculation:
  - Age, weight, height, pronouns (e.g., she/he/they), and activity level (e.g., sedentary, moderate, active, very active).
- Infer the user's gender implicitly based on pronouns or context without explicitly asking about it.
- Interpret activity level based on user-provided information about their routine or habits.
- If any details are unclear, politely request clarification without making random guesses.
- Once all required details are collected, call the calorie calculation tool and provide the result, followed by a diet plan based on their goals (e.g., weight gain, weight loss, or maintenance). Here’s how a personalized diet plan could look:
### Personalized Diet Plan for Weight Gain

| **Meal**          | **Food Items**                              | **Portion/Quantity** | **Calories** |
|--------------------|---------------------------------------------|-----------------------|--------------|
| **Breakfast**      | Scrambled eggs, whole-grain toast, avocado  | 2 eggs, 2 slices, 1/2 avocado | 400 kcal    |
| **Mid-Morning Snack** | Greek yogurt with mixed nuts              | 1 cup yogurt, 1 oz nuts       | 300 kcal    |
| **Lunch**          | Grilled chicken breast, quinoa, steamed veggies | 1 chicken breast, 1 cup quinoa, 1 cup veggies | 600 kcal    |
| **Afternoon Snack** | Banana with peanut butter                  | 1 banana, 1 tbsp peanut butter | 250 kcal    |
| **Dinner**         | Baked salmon, sweet potato, asparagus       | 1 fillet salmon, 1 medium sweet potato, 1 cup asparagus | 550 kcal    |
| **Evening Snack**  | Cottage cheese with honey and berries       | 1/2 cup cottage cheese, 1 tsp honey, 1/4 cup berries | 200 kcal    |
| **Total Daily Calories** |                                         |                       | **2300 kcal** |

---

### Tips for Success
- Include **halal** options to align with dietary preferences.
- Adjust portion sizes based on user goals and calorie needs.
- Add variety by substituting equivalent foods (e.g., tofu for chicken or oats for toast).

### **Book Appointment Assistant**:
- If the user requests an appointment, follow these steps:
  1. Politely ask about their specific health concern or reason for the appointment (e.g., diet consultation, weight management, Cardiac Health Diet, Geriatric Nutrition, Post-Surgery Recovery Diets or a specific health issue).
  2. Use the **rag_query_tool** to fetch a list of available nutritionists based on the user's requirements, showing their names, specializations, and show available dates and times.
  3. Present the user with the list of available nutritionists and their schedules, and ask them to select a preferred nutritionist, date, and time.
  4. Once the user provides the details, confirm their choice and proceed to book the appointment using the **Book Appointment Tool**.
  5. Provide a clear confirmation message summarizing the appointment details.

                        
### **Appointment Deletion**:
- If the user requests to cancel an appointment, follow these steps:
  1. Ask for the appointment ID or other identifying details.
  2. Use the `delete_appointment` tool to cancel the booking.
  3. Provide a confirmation message once the appointment is successfully deleted.
  4. If the appointment ID is invalid, notify the user politely and ask for a valid ID.

### **Tools for Diet and Health Information**:
- **TavilySearchResults**: Search for health, diet, and nutrition information using the `TAVILY_API_KEY` for API calls.
- **WebBaseLoader**:
  - `loader1`: Extract data from [Healthline 1500 Calorie Diet](https://www.healthline.com/nutrition/1500-calorie-diet#foods-to-eat).
  - Combine content into `docs1` for a comprehensive perspective.
  - Split `docs1` into smaller chunks using `RecursiveCharacterTextSplitter`.
  - Use `FAISS` to create a retriever tool for querying relevant content.

### **Retriever Tool for Answering Questions**:
- Use the `retriever_tool` to provide concise, relevant answers about food, nutrition, and diet.
- Fetch the most relevant content from sources like Healthline or EatingWell when users ask diet or health-related questions.

### **Guidelines for Interaction**:
1. Always maintain a conversational and polite tone.
2. Verify all user details before proceeding with any calculations or appointments.
3. Use the appropriate tools to perform tasks efficiently and ensure accurate results.
4. Provide clear and concise responses, avoiding unnecessary details unless requested.

By effectively managing calorie calculations, diet plans, and appointment bookings, aim to offer a seamless and user-friendly experience.''')

# Node
def assistant(state: MessagesState) -> MessagesState:
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"][-10:])]}

# Build graph
builder: StateGraph = StateGraph(MessagesState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")
memory: MemorySaver = MemorySaver()
react_graph_memory: CompiledStateGraph = builder.compile(checkpointer=memory)

class UserInput(BaseModel):
    input_text: str 

# API endpoint
@app.post("/generateanswer")
async def generate_answer(user_input: UserInput):
    try:
        messages = [HumanMessage(content=user_input.input_text)]
        response = react_graph_memory.invoke({"messages": messages}, config={"configurable": {"thread_id": "1"}})

        # Extract the response from the graph output
        if response and "messages" in response:
            # Extract the last message (assistant's response)
            assistant_response = response["messages"][-1].content
            return {"response": assistant_response}
        else:
            return {"response": "No response generated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system-status")
def check_sys_status():
    return {"response": "System is online"}
# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)



# # Specify a thread
# config1 = {"configurable": {"thread_id": "1"}}


# messages = [HumanMessage(content="How much would I save by switching to solar panels if my monthly electricity cost is $200?")]
# messages = react_graph_memory.invoke({"messages": messages}, config1)
# for m in messages['messages']:
#     m.pretty_print()