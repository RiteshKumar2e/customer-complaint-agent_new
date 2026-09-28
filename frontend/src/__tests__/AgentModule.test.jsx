import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("../api", () => ({
  getAgentQueue: jest.fn(),
  getComplaintDetail: jest.fn(),
  validateSolution: jest.fn(),
  sendResolution: jest.fn(),
  logoutUser: jest.fn(),
}));

import * as api from "../api";
import AgentModule from "../components/Agent/AgentModule";

const USER = { email: "agent@x.com", full_name: "Agent", role: "Admin" };
const QUEUE_ITEM = {
  ticket_id: "QX-20260928-AB12", name: "Asha", email: "asha@x.com", subject: "Double charge",
  category: "Billing", priority: "High", sentiment: "Negative", created_at: "2026-09-28T10:00:00", status: "pending",
};
const DETAIL = {
  complaint: {
    ...QUEUE_ITEM,
    description: "Charged twice",
    ai_solution: "1. Refund the duplicate charge.",
    ai_steps: [{ step: "Master Intelligence", status: "Done" }, "Issue refund"],
  },
  agent_resolution: null,
};

beforeEach(() => {
  api.getAgentQueue.mockResolvedValue({ complaints: [QUEUE_ITEM], total: 1 });
  api.getComplaintDetail.mockResolvedValue(DETAIL);
});

async function openTicket() {
  render(<AgentModule user={USER} onNavigate={jest.fn()} />);
  fireEvent.click(await screen.findByText(QUEUE_ITEM.ticket_id));
  await screen.findByDisplayValue(DETAIL.complaint.ai_solution);
}

test("loads the queue for the signed-in agent", async () => {
  render(<AgentModule user={USER} onNavigate={jest.fn()} />);
  expect(await screen.findByText(QUEUE_ITEM.ticket_id)).toBeInTheDocument();
  expect(api.getAgentQueue).toHaveBeenCalledWith("agent@x.com", expect.objectContaining({ status: "pending" }));
});

test("opening a ticket pre-fills the AI solution and flattens object steps", async () => {
  await openTicket();
  expect(api.getComplaintDetail).toHaveBeenCalledWith(QUEUE_ITEM.ticket_id, "agent@x.com");
  expect(screen.getByDisplayValue("Master Intelligence — Done")).toBeInTheDocument();
  expect(screen.getByDisplayValue("Issue refund")).toBeInTheDocument();
});

test("validation result is shown", async () => {
  api.validateSolution.mockResolvedValue({ approval_status: "approved", confidence_score: 0.92, validation_results: [] });
  await openTicket();

  fireEvent.click(screen.getByRole("button", { name: /validate with multi-model pipeline/i }));

  expect(await screen.findByText("APPROVED")).toBeInTheDocument();
  expect(screen.getByText(/92\.0%/)).toBeInTheDocument();
  expect(api.validateSolution).toHaveBeenCalledWith(
    "agent@x.com", QUEUE_ITEM.ticket_id, DETAIL.complaint.ai_solution, ["Master Intelligence — Done", "Issue refund"],
  );
});

test("rejected validation offers a force-deliver", async () => {
  api.validateSolution.mockResolvedValue({ approval_status: "rejected", confidence_score: 0.3, validation_results: [] });
  await openTicket();
  fireEvent.click(screen.getByRole("button", { name: /validate with multi-model pipeline/i }));
  expect(await screen.findByRole("button", { name: /force approve & deliver/i })).toBeInTheDocument();
});

test("delivering sends the edited solution and refreshes the queue", async () => {
  api.sendResolution.mockResolvedValue({ status: "delivered" });
  await openTicket();

  const editor = screen.getByDisplayValue(DETAIL.complaint.ai_solution);
  fireEvent.change(editor, { target: { value: "1. Refund issued today." } });
  fireEvent.click(screen.getByRole("button", { name: /approve & deliver to user/i }));

  await waitFor(() => expect(window.alert).toHaveBeenCalledWith("Resolution sent successfully!"));
  expect(api.sendResolution).toHaveBeenCalledWith(
    "agent@x.com", QUEUE_ITEM.ticket_id, "1. Refund issued today.", ["Master Intelligence — Done", "Issue refund"],
  );
  expect(api.getAgentQueue).toHaveBeenCalledTimes(2);
});

test("a failed delivery tells the agent why", async () => {
  api.sendResolution.mockRejectedValue({ response: { data: { detail: "Access denied. Agent role required." } } });
  await openTicket();
  fireEvent.click(screen.getByRole("button", { name: /approve & deliver to user/i }));
  await waitFor(() =>
    expect(window.alert).toHaveBeenCalledWith("Failed to send resolution: Access denied. Agent role required."),
  );
});

test("actions are disabled for an empty solution", async () => {
  await openTicket();
  fireEvent.change(screen.getByDisplayValue(DETAIL.complaint.ai_solution), { target: { value: "   " } });
  expect(screen.getByRole("button", { name: /validate with multi-model pipeline/i })).toBeDisabled();
  expect(screen.getByRole("button", { name: /approve & deliver to user/i })).toBeDisabled();
});
