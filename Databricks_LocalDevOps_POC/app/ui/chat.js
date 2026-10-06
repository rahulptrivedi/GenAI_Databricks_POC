"use strict";

const form = document.querySelector("#question-form");
const question = document.querySelector("#question");
const messages = document.querySelector("#messages");
const statusLine = document.querySelector("#status");
const sendButton = document.querySelector("#send");
let conversationId = null;

function addText(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function showResponse(response) {
  const message = document.createElement("article");
  message.className = "message assistant";
  addText(message, "p", "message-label", "CATALOG ASSISTANT");
  addText(message, "div", "message-body", response.answer);

  const meta = document.createElement("div");
  meta.className = "message-meta";
  addText(meta, "span", "", `Status: ${response.status.replaceAll("_", " ")}`);
  response.sources.forEach((source) => addText(meta, "span", "source", source.object_name));
  response.warnings.forEach((warning) => addText(meta, "span", "warning", warning));
  addText(meta, "span", "", `Request ${response.correlation_id.slice(0, 8)}`);

  const feedback = document.createElement("span");
  feedback.className = "feedback";
  [["helpful", "Helpful"], ["not_helpful", "Not helpful"]].forEach(([rating, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.title = label;
    button.setAttribute("aria-label", label);
    button.textContent = rating === "helpful" ? "+" : "-";
    button.addEventListener("click", () => submitFeedback(response.correlation_id, rating));
    feedback.append(button);
  });
  meta.append(feedback);
  message.append(meta);

  if (response.supporting_sql) {
    const details = document.createElement("details");
    details.className = "sql-details";
    addText(details, "summary", "", "Supporting SQL");
    addText(details, "pre", "", response.supporting_sql);
    message.append(details);
  }
  messages.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function submitFeedback(correlationId, rating) {
  try {
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correlation_id: correlationId, rating }),
    });
  } catch {
    statusLine.textContent = "Feedback could not be recorded.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const userQuestion = question.value.trim();
  if (!userQuestion) return;

  const userMessage = document.createElement("article");
  userMessage.className = "message user";
  addText(userMessage, "p", "message-label", "YOU");
  addText(userMessage, "div", "message-body", userQuestion);
  messages.append(userMessage);

  question.value = "";
  question.disabled = true;
  sendButton.disabled = true;
  statusLine.className = "status";
  statusLine.textContent = "Checking the catalog...";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userQuestion, conversation_id: conversationId }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The request could not be completed.");
    conversationId = payload.conversation_id || conversationId;
    showResponse(payload);
    statusLine.textContent = "";
  } catch (error) {
    statusLine.className = "status error";
    statusLine.textContent = error.message;
  } finally {
    question.disabled = false;
    sendButton.disabled = false;
    question.focus();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    question.value = button.textContent;
    question.focus();
  });
});

document.querySelector("#reset").addEventListener("click", () => {
  conversationId = null;
  messages.replaceChildren();
  statusLine.textContent = "New conversation started.";
  question.focus();
});

fetch("/api/config")
  .then((response) => response.json())
  .then((config) => { question.maxLength = config.question_max_chars; })
  .catch(() => {});
