'use client'
import React, { useState } from "react";
import { Label } from "./components/ui/label";
import { Input } from "./components/ui/input";
import { cn } from "./lib/utils";
import {
  IconBrandGithub,
  IconBrandGoogle,
  IconBrandOnlyfans,
} from "@tabler/icons-react";

export default function SignupFormDemo() {
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    First_Name: "",
    Last_Name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formData.First_Name.trim() || !formData.Last_Name.trim() || !formData.email.trim() || !formData.password.trim() || !formData.confirm_password.trim()) return;

    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8056/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (response.status === 409) {
          alert("Email is already registered.");
          window.location.href = "/chatbot";
      } else if (data.response) {
          alert("User registered successfully");
          // Redirect to chatbot page here
          window.location.href = "/chatbot";  // or use next/router for page routing
      } else {
          alert("Registration failed: " + data.message || "Unknown error");
      }
    } catch (err) {
      console.log("error", err);
      alert("Error: Unable to register.");
    }

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex justify-center items-center bg-gradient-to-br from-pink-800 via-black to-brown-900 py-12">
      <div className="max-w-md w-full mx-auto rounded-none md:rounded-2xl p-4 md:p-8 shadow-input bg-gradient-to-br from-white via-brown-500 to-brown-400 dark:from-gray-900 dark:via-black dark:to-brown-700 text-white">
        <h2 className="font-bold text-xl text-neutral-100">Welcome to Aceternity</h2>
        <p className="text-neutral-300 text-sm max-w-sm mt-2">
          Login to aceternity if you can because we don&apos;t have a login flow yet
        </p>

        <form className="my-8" onSubmit={handleSubmit}>
          <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-2 mb-4">
            <LabelInputContainer>
              <Label htmlFor="First_Name">First name</Label>
              <Input
                id="First_Name"
                name="First_Name"
                value={formData.First_Name}
                onChange={handleInputChange}
                placeholder="Tyler"
                type="text"
              />
            </LabelInputContainer>
            <LabelInputContainer>
              <Label htmlFor="Last_Name">Last name</Label>
              <Input
                id="Last_Name"
                name="Last_Name"
                value={formData.Last_Name}
                onChange={handleInputChange}
                placeholder="Durden"
                type="text"
              />
            </LabelInputContainer>
          </div>
          <LabelInputContainer className="mb-4">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="projectmayhem@fc.com"
              type="email"
            />
          </LabelInputContainer>
          <LabelInputContainer className="mb-4">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="••••••••"
              type="password"
            />
          </LabelInputContainer>
          <LabelInputContainer className="mb-8">
            <Label htmlFor="confirm_password">Confirm Password</Label>
            <Input
              id="confirm_password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleInputChange}
              placeholder="••••••••"
              type="password"
            />
          </LabelInputContainer>

          <button
            className="bg-gradient-to-br from-purple-700 to-purple-500 block w-full text-white rounded-md h-10 font-medium shadow-[0px_1px_0px_0px_#ffffff40_inset,0px_-1px_0px_0px_#ffffff40_inset] dark:shadow-[0px_1px_0px_0px_var(--zinc-800)_inset,0px_-1px_0px_0px_var(--zinc-800)_inset] flex items-center justify-center"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? (
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                ></path>
              </svg>
            ) : (
              "Sign up →"
            )}
          </button>

          <div className="bg-gradient-to-r from-transparent via-neutral-500 dark:via-neutral-700 to-transparent my-8 h-[1px] w-full" />

          <div className="flex flex-col space-y-4">
            <button
              className="relative group/btn flex space-x-2 items-center justify-start px-4 w-full text-white rounded-md h-10 font-medium shadow-input bg-gray-700 dark:bg-zinc-800"
              type="submit"
            >
              <IconBrandGithub className="h-4 w-4 text-neutral-100" />
              <span className="text-neutral-200 text-sm">GitHub</span>
              <BottomGradient />
            </button>
            <button
              className="relative group/btn flex space-x-2 items-center justify-start px-4 w-full text-white rounded-md h-10 font-medium shadow-input bg-gray-700 dark:bg-zinc-800"
              type="submit"
            >
              <IconBrandGoogle className="h-4 w-4 text-neutral-100" />
              <span className="text-neutral-200 text-sm">Google</span>
              <BottomGradient />
            </button>
            <button
              className="relative group/btn flex space-x-2 items-center justify-start px-4 w-full text-white rounded-md h-10 font-medium shadow-input bg-gray-700 dark:bg-zinc-800"
              type="submit"
            >
              <IconBrandOnlyfans className="h-4 w-4 text-neutral-100" />
              <span className="text-neutral-200 text-sm">OnlyFans</span>
              <BottomGradient />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const BottomGradient = () => {
  return (
    <>
      <span className="group-hover/btn:opacity-100 block transition duration-500 opacity-0 absolute h-px w-full -bottom-px inset-x-0 bg-gradient-to-r from-transparent via-cyan-500 to-transparent" />
      <span className="group-hover/btn:opacity-100 blur-sm block transition duration-500 opacity-0 absolute h-px w-1/2 mx-auto -bottom-px inset-x-10 bg-gradient-to-r from-transparent via-indigo-500 to-transparent" />
    </>
  );
};

const LabelInputContainer = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <div className={cn("flex flex-col space-y-2 w-full", className)}>
      {children}
    </div>
  );
};
