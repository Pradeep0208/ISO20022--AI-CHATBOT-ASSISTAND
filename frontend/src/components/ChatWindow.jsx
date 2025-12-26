import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { sendMessageToBackend } from "../api/apiClient";

const INITIAL_MESSAGES = [
  {
    text: `Welcome! 👋
I'm your ISO 20022 Assistant, here to help you understand PAIN, PACS, and CAMT messages clearly and accurately.

You can ask me about:
• Message definitions & usage (e.g., "What is pacs.004?")
• Message building blocks (e.g., "What is MessageIdentification <MsgId> in message building blocks of pacs.002?")
• Constraints & validation rules (e.g., "What are the constraints in pain.001?")
• Message structure & specific fields

Just type your question to get started.`,
    sender: "bot",
    singleSpacing: true,
  },
];


export default function ChatWindow() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  useEffect(() => {
    window.__ISO_CHAT_DARK_MODE__ = darkMode;
  }, [darkMode]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage = { text: trimmed, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    autoResizeTextarea("");

    setIsLoading(true);

    try {
      const response = await sendMessageToBackend(trimmed);

      const botMessage = {
        text: response.answer,
        sender: "bot",
        singleSpacing: true,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error talking to backend:", error);

      const errorMessage = {
        text:
          "Sorry, I couldn't reach the ISO 20022 service. " +
          "Please make sure the FastAPI backend is running.",
        sender: "bot",
        singleSpacing: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const autoResizeTextarea = (value) => {
    if (!textareaRef.current) return;
    const el = textareaRef.current;
    el.style.height = "0px";
    const newHeight = Math.min(el.scrollHeight, 140);
    el.style.height = newHeight + "px";
    if (value !== undefined) {
      setInput(value);
    }
  };

  const handleClear = () => {
    setMessages(INITIAL_MESSAGES);
  };

  const toggleDarkMode = () => {
    setDarkMode((prev) => !prev);
  };

  // Professional Color Palette
  const pageBg = darkMode ? "#0f172a" : "#f8fafc";
  const cardBg = darkMode ? "#1e293b" : "#ffffff";
  const cardBorder = darkMode ? "#334155" : "#e2e8f0";
  const headerBg = darkMode ? "#1e3a5f" : "#1e40af";
  const titleColor = darkMode ? "#f1f5f9" : "#ffffff";
  const subTitleColor = darkMode ? "#cbd5e1" : "#e0e7ff";
  const inputBg = darkMode ? "#0f172a" : "#ffffff";
  const inputBorder = darkMode ? "#475569" : "#cbd5e1";
  const inputText = darkMode ? "#f1f5f9" : "#1e293b";
  const buttonBg = darkMode ? "#2563eb" : "#1e40af";
  const buttonHoverBg = darkMode ? "#1d4ed8" : "#1e3a8a";
  const hintTextColor = darkMode ? "#94a3b8" : "#64748b";

  return (
    <>
      <style>{`
        * {
          font-family: 'Times New Roman', Times, serif;
          font-size: 12px;
        }

        /* All headings in chat content: same size as body text */
        h1, h2, h3, h4, h5, h6 {
          font-size: 12px;
          font-weight: bold;
          margin: 0.4em 0;
        }

        p {
          margin: 0.4em 0;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .btn-professional {
          transition: all 0.2s ease;
        }

        .btn-professional:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .btn-professional:active:not(:disabled) {
          transform: translateY(0);
        }

        .chat-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .chat-scrollbar::-webkit-scrollbar-track {
          background: ${darkMode ? "#1e293b" : "#f1f5f9"};
          border-radius: 4px;
        }

        .chat-scrollbar::-webkit-scrollbar-thumb {
          background: ${darkMode ? "#475569" : "#cbd5e1"};
          border-radius: 4px;
        }

        .chat-scrollbar::-webkit-scrollbar-thumb:hover {
          background: ${darkMode ? "#64748b" : "#94a3b8"};
        }
      `}</style>

      <div
        style={{
          minHeight: "100vh",
          backgroundColor: pageBg,
          color: inputText,
          padding: "32px 24px",
          boxSizing: "border-box",
          transition: "background-color 0.3s ease",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "1100px",
            margin: "0 auto",
            animation: "fadeIn 0.4s ease-out",
          }}
        >
          {/* Professional Header */}
          <div
            style={{
              backgroundColor: headerBg,
              borderRadius: "12px 12px 0 0",
              padding: "24px 32px",
              boxShadow: darkMode
                ? "0 4px 20px rgba(0, 0, 0, 0.3)"
                : "0 2px 8px rgba(30, 64, 175, 0.1)",
              borderBottom: `3px solid ${darkMode ? "#3b82f6" : "#1e3a8a"}`,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <h1
                  style={{
                    margin: 0,
                    fontSize: "28px",
                    fontWeight: 700,
                    color: titleColor,
                    letterSpacing: "-0.02em",
                  }}
                >
                  ISO 20022 Documentation Assistant
                </h1>
                <p
                  style={{
                    margin: "8px 0 0 0",
                    fontSize: "14px",
                    color: subTitleColor,
                    fontWeight: 500,
                  }}
                >
                  Expert guidance on payment message standards • PAIN, PACS, CAMT
                </p>
              </div>

              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <button
                  onClick={toggleDarkMode}
                  className="btn-professional"
                  style={{
                    padding: "10px 18px",
                    borderRadius: "8px",
                    border: "none",
                    backgroundColor: darkMode
                      ? "rgba(255, 255, 255, 0.1)"
                      : "rgba(255, 255, 255, 0.2)",
                    color: titleColor,
                    cursor: "pointer",
                    fontSize: "13px",
                    fontWeight: 600,
                    backdropFilter: "blur(8px)",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  {darkMode ? "☀️" : "🌙"}
                  <span>{darkMode ? "Light" : "Dark"}</span>
                </button>

                <button
                  onClick={handleClear}
                  className="btn-professional"
                  style={{
                    padding: "10px 18px",
                    borderRadius: "8px",
                    border: "none",
                    backgroundColor: darkMode
                      ? "rgba(255, 255, 255, 0.1)"
                      : "rgba(255, 255, 255, 0.2)",
                    color: titleColor,
                    cursor: "pointer",
                    fontSize: "13px",
                    fontWeight: 600,
                    backdropFilter: "blur(8px)",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  🗑️
                  <span>Clear</span>
                </button>
              </div>
            </div>
          </div>

          {/* Main Chat Container */}
          <div
            style={{
              backgroundColor: cardBg,
              borderRadius: "0 0 12px 12px",
              border: `1px solid ${cardBorder}`,
              borderTop: "none",
              display: "flex",
              flexDirection: "column",
              height: "650px",
              overflow: "hidden",
              boxShadow: darkMode
                ? "0 8px 32px rgba(0, 0, 0, 0.4)"
                : "0 2px 12px rgba(0, 0, 0, 0.08)",
            }}
          >
            {/* Chat Messages Area */}
            <div
              className="chat-scrollbar"
              style={{
                flex: 1,
                padding: "28px 32px",
                overflowY: "auto",
                backgroundColor: darkMode ? "#0f172a" : "#f8fafc",
              }}
            >
              {messages.map((msg, idx) => (
                <MessageBubble
                  key={idx}
                  text={msg.text}
                  sender={msg.sender}
                  darkMode={darkMode}
                  singleSpacing={msg.singleSpacing}
                />
              ))}

              {isLoading && (
                <MessageBubble
                  text=""
                  sender="bot"
                  isTyping={true}
                  darkMode={darkMode}
                />
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div
              style={{
                borderTop: `2px solid ${cardBorder}`,
                padding: "20px 32px 24px 32px",
                backgroundColor: cardBg,
              }}
            >
              <div
                style={{
                  fontSize: "12px",
                  color: hintTextColor,
                  marginBottom: "10px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontWeight: 500,
                }}
              >
                <span>💬 Press Enter to send • Shift + Enter for new line</span>
                {isLoading && (
                  <span
                    style={{
                      color: darkMode ? "#60a5fa" : "#2563eb",
                      animation: "pulse 1.5s ease-in-out infinite",
                    }}
                  >
                    ⚡ Processing...
                  </span>
                )}
              </div>

              <div
                style={{
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-end",
                }}
              >
                <textarea
                  ref={textareaRef}
                  style={{
                    flex: 1,
                    minHeight: "52px",
                    maxHeight: 140,
                    resize: "none",
                    padding: "14px 16px",
                    borderRadius: "10px",
                    border: `2px solid ${inputBorder}`,
                    backgroundColor: inputBg,
                    color: inputText,
                    outline: "none",
                    fontSize: "15px",
                    lineHeight: 1.5,
                    fontFamily: "inherit",
                    boxShadow: darkMode
                      ? "0 2px 8px rgba(0, 0, 0, 0.2)"
                      : "0 1px 3px rgba(0, 0, 0, 0.08)",
                    transition: "border-color 0.2s ease, box-shadow 0.2s ease",
                  }}
                  value={input}
                  placeholder="Ask about message types, structures, constraints, or specific fields..."
                  onChange={(e) => autoResizeTextarea(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={(e) => {
                    e.target.style.borderColor = darkMode ? "#3b82f6" : "#2563eb";
                    e.target.style.boxShadow = darkMode
                      ? "0 0 0 3px rgba(59, 130, 246, 0.1)"
                      : "0 0 0 3px rgba(37, 99, 235, 0.1)";
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = inputBorder;
                    e.target.style.boxShadow = darkMode
                      ? "0 2px 8px rgba(0, 0, 0, 0.2)"
                      : "0 1px 3px rgba(0, 0, 0, 0.08)";
                  }}
                />

                <button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="btn-professional"
                  style={{
                    padding: "14px 28px",
                    borderRadius: "10px",
                    backgroundColor: isLoading || !input.trim() 
                      ? (darkMode ? "#475569" : "#cbd5e1")
                      : buttonBg,
                    color: "white",
                    border: "none",
                    cursor: isLoading || !input.trim() ? "not-allowed" : "pointer",
                    fontSize: "15px",
                    fontWeight: 600,
                    minWidth: "100px",
                    boxShadow: isLoading || !input.trim()
                      ? "none"
                      : darkMode
                      ? "0 4px 12px rgba(37, 99, 235, 0.3)"
                      : "0 2px 8px rgba(30, 64, 175, 0.2)",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (!isLoading && input.trim()) {
                      e.target.style.backgroundColor = buttonHoverBg;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isLoading && input.trim()) {
                      e.target.style.backgroundColor = buttonBg;
                    }
                  }}
                >
                  {isLoading ? "..." : "Send →"}
                </button>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div
            style={{
              marginTop: "20px",
              padding: "16px",
              textAlign: "center",
              fontSize: "13px",
              color: hintTextColor,
              backgroundColor: darkMode ? "#1e293b" : "#ffffff",
              borderRadius: "8px",
              border: `1px solid ${cardBorder}`,
            }}
          >
            Built with expertise by <strong>Pradeep</strong> • Showcasing
            full-stack development and ISO 20022 knowledge
          </div>
        </div>
      </div>
    </>
  );
}