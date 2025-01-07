"use client";

import { useState } from "react";
// import Typewriter from "typewriter-effect";
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Define the Message type
interface Message {
  type: "user" | "bot";
  text: string;
}

const ChatPage = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Add user input to chat
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "user", text: input },
    ]);

    setLoading(true);

    try {
      // Make POST request to the FastAPI endpoint
      const response = await fetch("http://127.0.0.1:8009/generateanswer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ input_text: input }),
      });

      const data = await response.json();

      if (data.response) {
        // Add bot response to chat
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "bot", text: data.response },
        ]);
      } else {
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "bot", text: "No response generated." },
        ]);
      }
    } catch (err) {
      // Handle errors
      console.log("error", err);
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "bot", text: "Error: Unable to fetch response." },
      ]);
    }

    setInput(""); // Clear input field
    setLoading(false); // Stop loading
  };

  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen bg-cover bg-center py-8"
      style={{ backgroundImage: "url(/newBg.jpg)" }}
    >
      <div className="m-4 w-full">
        <section className="mb-6  text-center">
          <h1 className="text-3xl font-bold text-white">Nutritionist</h1>
          <h6 className="text-sm text-white">
            Your AI Powered nutrition planner assistant
          </h6>
        </section>

        <section className="mb-4 w-auto mx-4 sm:w-4/6 md:w-3/6 sm:m-auto">
          <div className="bg-white bg-opacity-20 backdrop-blur-md border border-gray-300 rounded-md p-3 h-96 overflow-y-auto flex flex-col">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`my-2 p-2 rounded-lg ${
                  msg.type === "user"
                    ? "bg-red-600 bg-opacity-80 backdrop-blur-md text-white self-end"
                    : "bg-gray-200 text-black self-start"
                }`}
              >
                {msg.type === "user" ? 
                  msg.text:
                  <Markdown remarkPlugins={[remarkGfm]}>{msg.text}</Markdown>
                }
              </div>
            ))}
          </div>
          <section className="flex flex-col w-full mt-2">
            <form onSubmit={handleSubmit} className="flex flex-col">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="p-2 border border-gray-300 rounded-lg mb-2"
                placeholder="What is your goal?"
                required
              />
              <button
                type="submit"
                className={`p-2 rounded-lg flex cursor-pointer items-center justify-center ${
                  loading ? "bg-gray-500" : "bg-red-600 hover:bg-red-700"
                } text-white`}
                disabled={loading}
              >
                {loading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 0016 0H4z"
                    />
                  </svg>
                ) : (
                  "Submit"
                )}
              </button>
            </form>
          </section>
        </section>
      </div>
    </div>
  );
};

export default ChatPage;
