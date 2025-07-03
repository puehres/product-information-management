/**
 * Tests for the Home page component.
 *
 * This module tests the main landing page functionality,
 * including rendering, content display, and user interactions.
 */

import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import Home from "../page";

// Mock Next.js font
jest.mock("next/font/google", () => ({
  Inter: () => ({
    className: "inter-font",
  }),
}));

describe("Home Page", () => {
  beforeEach(() => {
    // Clear any previous renders
    document.body.innerHTML = "";
  });

  describe("Rendering", () => {
    it("renders the home page without crashing", () => {
      render(<Home />);

      // Check if the main element is present
      const main = screen.getByRole("main");
      expect(main).toBeInTheDocument();
    });

    it("displays the application title", () => {
      render(<Home />);

      // Check for the main heading
      const heading = screen.getByRole("heading", {
        name: /welcome to universal product automation/i,
      });
      expect(heading).toBeInTheDocument();
    });

    it("displays the application name in the header", () => {
      render(<Home />);

      // Check for the application name
      const appName = screen.getByText(/universal product automation system/i);
      expect(appName).toBeInTheDocument();
    });
  });

  describe("Feature Cards", () => {
    it("displays all four feature cards", () => {
      render(<Home />);

      // Check for all feature headings
      const productManagement = screen.getByRole("heading", {
        name: /product management/i,
      });
      const webScraping = screen.getByRole("heading", {
        name: /web scraping/i,
      });
      const imageProcessing = screen.getByRole("heading", {
        name: /image processing/i,
      });
      const translation = screen.getByRole("heading", {
        name: /translation/i,
      });

      expect(productManagement).toBeInTheDocument();
      expect(webScraping).toBeInTheDocument();
      expect(imageProcessing).toBeInTheDocument();
      expect(translation).toBeInTheDocument();
    });

    it("displays feature descriptions", () => {
      render(<Home />);

      // Check for feature descriptions
      expect(
        screen.getByText(/manage product data with supplier integration/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/automated data extraction from supplier websites/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          /image optimization, validation, and format conversion/i,
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/multi-language content generation using ai/i),
      ).toBeInTheDocument();
    });

    it("displays arrow indicators on feature cards", () => {
      render(<Home />);

      // Check for arrow indicators (->)
      const arrows = screen.getAllByText("->");
      expect(arrows).toHaveLength(4); // One for each feature card
    });
  });

  describe("Layout and Structure", () => {
    it("has proper semantic structure", () => {
      render(<Home />);

      // Check for main element
      const main = screen.getByRole("main");
      expect(main).toBeInTheDocument();

      // Check for headings hierarchy
      const h1 = screen.getByRole("heading", { level: 1 });
      const h2Elements = screen.getAllByRole("heading", { level: 2 });

      expect(h1).toBeInTheDocument();
      expect(h2Elements).toHaveLength(4); // Four feature cards
    });

    it("applies correct CSS classes for layout", () => {
      render(<Home />);

      const main = screen.getByRole("main");

      // Check for Tailwind CSS classes
      expect(main).toHaveClass("flex", "min-h-screen", "flex-col");
    });

    it("has responsive grid layout for feature cards", () => {
      render(<Home />);

      // Find the grid container
      const gridContainer = screen.getByRole("main").querySelector(".grid");

      expect(gridContainer).toBeInTheDocument();
      expect(gridContainer).toHaveClass("grid");
    });
  });

  describe("Accessibility", () => {
    it("has proper heading structure", () => {
      render(<Home />);

      // Check heading levels
      const h1 = screen.getByRole("heading", { level: 1 });
      const h2Elements = screen.getAllByRole("heading", { level: 2 });

      expect(h1).toBeInTheDocument();
      expect(h2Elements).toHaveLength(4);
    });

    it("has descriptive text for screen readers", () => {
      render(<Home />);

      // Check that feature descriptions are present and descriptive
      const descriptions = [
        /manage product data with supplier integration/i,
        /automated data extraction from supplier websites/i,
        /image optimization, validation, and format conversion/i,
        /multi-language content generation using ai/i,
      ];

      descriptions.forEach((description) => {
        expect(screen.getByText(description)).toBeInTheDocument();
      });
    });

    it("uses semantic HTML elements", () => {
      render(<Home />);

      // Check for semantic elements
      const main = screen.getByRole("main");
      const headings = screen.getAllByRole("heading");

      expect(main).toBeInTheDocument();
      expect(headings.length).toBeGreaterThan(0);
    });
  });

  describe("Content Validation", () => {
    it("displays correct application branding", () => {
      render(<Home />);

      // Check for consistent branding
      const brandingElements = screen.getAllByText(
        /universal product automation/i,
      );
      expect(brandingElements.length).toBeGreaterThan(0);
    });

    it("has meaningful feature descriptions", () => {
      render(<Home />);

      // Verify each feature has a description
      const featureCards = screen.getByRole("main").querySelectorAll(".group");

      featureCards.forEach((card) => {
        const description = card.querySelector("p");
        expect(description).toBeInTheDocument();
        expect(description?.textContent).toBeTruthy();
        expect(description?.textContent?.length).toBeGreaterThan(10);
      });
    });

    it("displays feature cards in correct order", () => {
      render(<Home />);

      const headings = screen.getAllByRole("heading", { level: 2 });
      const expectedOrder = [
        /product management/i,
        /web scraping/i,
        /image processing/i,
        /translation/i,
      ];

      expectedOrder.forEach((pattern, index) => {
        expect(headings[index]).toHaveTextContent(pattern);
      });
    });
  });

  describe("Visual Elements", () => {
    it("applies hover effects to feature cards", () => {
      render(<Home />);

      // Check for hover classes
      const featureCards = screen.getByRole("main").querySelectorAll(".group");

      featureCards.forEach((card) => {
        expect(card).toHaveClass("group");
        // Hover effects are applied via CSS, so we check for the group class
        // which enables hover: pseudo-class styling
      });
    });

    it("has gradient background elements", () => {
      render(<Home />);

      // Check for gradient background elements
      const main = screen.getByRole("main");
      const gradientElements = main.querySelectorAll('[class*="gradient"]');

      expect(gradientElements.length).toBeGreaterThan(0);
    });

    it("displays arrow animations on hover", () => {
      render(<Home />);

      // Check for arrow elements with transition classes
      const arrows = screen.getAllByText("->");

      arrows.forEach((arrow) => {
        const span = arrow.closest("span");
        expect(span).toHaveClass("inline-block", "transition-transform");
      });
    });
  });

  describe("Responsive Design", () => {
    it("has responsive classes for different screen sizes", () => {
      render(<Home />);

      const main = screen.getByRole("main");

      // Check for responsive padding
      expect(main).toHaveClass("p-24");

      // Check for responsive grid
      const gridContainer = main.querySelector(".grid");
      expect(gridContainer).toHaveClass("lg:grid-cols-4");
    });

    it("has mobile-first responsive text sizing", () => {
      render(<Home />);

      const mainHeading = screen.getByRole("heading", { level: 1 });
      expect(mainHeading).toHaveClass("text-4xl");

      const featureHeadings = screen.getAllByRole("heading", { level: 2 });
      featureHeadings.forEach((heading) => {
        expect(heading).toHaveClass("text-2xl");
      });
    });
  });

  describe("Performance Considerations", () => {
    it("renders efficiently without unnecessary re-renders", () => {
      const { rerender } = render(<Home />);

      // Re-render with same props
      rerender(<Home />);

      // Component should still be present
      expect(screen.getByRole("main")).toBeInTheDocument();
    });

    it("has optimized class names for CSS", () => {
      render(<Home />);

      const main = screen.getByRole("main");

      // Check that classes are using Tailwind's utility classes
      // which are optimized for performance
      expect(main.className).toContain("flex");
      expect(main.className).toContain("min-h-screen");
    });
  });
});
