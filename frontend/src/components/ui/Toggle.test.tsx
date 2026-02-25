import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Toggle } from "./Toggle";

describe("Toggle", () => {
  it("renders with label", () => {
    render(<Toggle checked={false} onChange={() => {}} label="Enable" />);
    expect(screen.getByText("Enable")).toBeInTheDocument();
  });

  it("reflects checked state via aria-checked", () => {
    render(<Toggle checked={true} onChange={() => {}} />);
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");
  });

  it("reflects unchecked state", () => {
    render(<Toggle checked={false} onChange={() => {}} />);
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "false");
  });

  it("calls onChange when clicked", async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(<Toggle checked={false} onChange={handleChange} />);
    await user.click(screen.getByRole("switch"));
    expect(handleChange).toHaveBeenCalledWith(true);
  });

  it("passes opposite value on toggle", async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(<Toggle checked={true} onChange={handleChange} />);
    await user.click(screen.getByRole("switch"));
    expect(handleChange).toHaveBeenCalledWith(false);
  });

  it("does not fire when disabled", async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(<Toggle checked={false} onChange={handleChange} disabled />);
    await user.click(screen.getByRole("switch"));
    expect(handleChange).not.toHaveBeenCalled();
  });
});
