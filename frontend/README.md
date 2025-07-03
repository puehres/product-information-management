# Universal Product Automation System - Frontend

Next.js-based frontend for the Universal Product Automation System, providing a modern, responsive user interface for product data management, web scraping, image processing, and multi-language content generation.

## Features

- **Modern UI/UX**: Built with Next.js 14, React 18, and Tailwind CSS
- **Type Safety**: Full TypeScript support with strict type checking
- **Component Library**: Shadcn/UI components with Radix UI primitives
- **State Management**: React Query for server state management
- **Form Handling**: React Hook Form with Zod validation
- **File Uploads**: React Dropzone for drag-and-drop file handling
- **Responsive Design**: Mobile-first responsive design with Tailwind CSS
- **Dark Mode**: Built-in dark mode support
- **Performance**: Optimized with Next.js App Router and SWC

## Technology Stack

- **Framework**: Next.js 14.0.4 with App Router
- **UI Library**: React 18.2.0 with TypeScript 5.3.3
- **Styling**: Tailwind CSS 3.3.6 with custom design system
- **Components**: Shadcn/UI with Radix UI primitives
- **Icons**: Lucide React for consistent iconography
- **State Management**: TanStack React Query 5.14.2
- **Forms**: React Hook Form 7.48.2 with Zod validation
- **HTTP Client**: Axios 1.6.2 for API communication
- **File Handling**: React Dropzone 14.2.3
- **Notifications**: React Hot Toast 2.4.1
- **Testing**: Jest 29.7.0 with React Testing Library

## Project Structure

```
frontend/
├── src/
│   ├── app/                   # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout component
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/            # Reusable UI components (future)
│   ├── lib/                   # Utility functions and configurations (future)
│   ├── hooks/                 # Custom React hooks (future)
│   ├── types/                 # TypeScript type definitions (future)
│   └── utils/                 # Helper functions (future)
├── public/                    # Static assets
├── package.json               # Dependencies and scripts
├── next.config.js            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── postcss.config.js         # PostCSS configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Quick Start

### Prerequisites

- Node.js 18.0.0 or higher
- npm 8.0.0 or higher

### Installation

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Set up environment variables**:

   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```

The application will be available at:

- **Frontend**: http://localhost:3000
- **API Proxy**: http://localhost:3000/api (proxied to backend)

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env.local` and update the values:

### Required Configuration

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Configuration
NEXT_PUBLIC_APP_NAME=Universal Product Automation System
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Optional Configuration

```bash
# Development
NODE_ENV=development

# Feature Flags (for future use)
NEXT_PUBLIC_ENABLE_DARK_MODE=true
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

## Available Scripts

### Development

```bash
# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Code formatting
npm run format
npm run format:check
```

### Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Production

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Development Guidelines

### Code Style

The project uses several tools to maintain code quality:

- **ESLint**: Linting with Next.js and TypeScript rules
- **Prettier**: Code formatting with Tailwind CSS plugin
- **TypeScript**: Strict type checking enabled

### Component Development

- Use functional components with hooks
- Implement proper TypeScript interfaces
- Follow the component structure:

  ```tsx
  interface ComponentProps {
    // Define props with proper types
  }

  export function Component({ prop }: ComponentProps) {
    // Component logic
    return (
      // JSX with proper accessibility
    );
  }
  ```

### Styling Guidelines

- Use Tailwind CSS utility classes
- Follow the custom design system defined in `tailwind.config.js`
- Use CSS variables for theme consistency
- Implement responsive design with mobile-first approach

### State Management

- Use React Query for server state
- Use React hooks for local component state
- Implement proper error handling and loading states

## API Integration

The frontend communicates with the backend API through:

- **Base URL**: Configured via `NEXT_PUBLIC_API_URL`
- **Proxy**: Next.js rewrites API requests during development
- **HTTP Client**: Axios with interceptors for error handling
- **State Management**: React Query for caching and synchronization

### API Endpoints (Planned)

```typescript
// Product Management
GET    /api/v1/products
POST   /api/v1/products
PUT    /api/v1/products/:id
DELETE /api/v1/products/:id

// Supplier Management
GET    /api/v1/suppliers
POST   /api/v1/suppliers

// Web Scraping
POST   /api/v1/scraping/start
GET    /api/v1/scraping/status/:id

// Batch Processing
POST   /api/v1/processing/batch
GET    /api/v1/processing/status/:id
```

## UI Components

The application uses Shadcn/UI components built on Radix UI primitives:

- **Form Components**: Input, Select, Checkbox, Switch
- **Navigation**: Tabs, Dropdown Menu, Dialog
- **Feedback**: Toast, Tooltip, Alert
- **Layout**: Card, Separator, Container
- **Data Display**: Table, Badge, Avatar

### Custom Components (Future)

- **ProductCard**: Display product information
- **FileUploader**: Drag-and-drop file upload
- **DataTable**: Sortable and filterable data tables
- **StatusIndicator**: Processing status display
- **ImageGallery**: Product image management

## Responsive Design

The application is built with a mobile-first approach:

- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

Key responsive features:

- Adaptive navigation
- Flexible grid layouts
- Touch-friendly interactions
- Optimized image loading

## Performance Optimization

- **Next.js App Router**: Optimized routing and rendering
- **Image Optimization**: Next.js Image component with WebP/AVIF
- **Code Splitting**: Automatic code splitting by route
- **Bundle Analysis**: Webpack bundle analyzer (optional)
- **Caching**: React Query for API response caching

## Accessibility

The application follows WCAG 2.1 guidelines:

- **Semantic HTML**: Proper heading structure and landmarks
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and descriptions
- **Color Contrast**: Meets AA contrast requirements
- **Focus Management**: Visible focus indicators

## Testing

### Testing Strategy

- **Unit Tests**: Component logic and utilities
- **Integration Tests**: Component interactions
- **E2E Tests**: Critical user flows (future)

### Testing Tools

- **Jest**: Test runner and assertion library
- **React Testing Library**: Component testing utilities
- **Jest DOM**: Additional DOM matchers
- **User Event**: User interaction simulation

### Example Test

```typescript
import { render, screen } from '@testing-library/react'
import { Component } from './Component'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })
})
```

## Deployment

### Build Process

```bash
# Install dependencies
npm ci

# Run type checking
npm run type-check

# Run linting
npm run lint

# Run tests
npm test

# Build for production
npm run build
```

### Environment Variables for Production

```bash
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_NAME=Universal Product Automation System
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Deployment Options

- **Vercel**: Optimized for Next.js applications
- **Netlify**: Static site deployment with serverless functions
- **Docker**: Containerized deployment
- **Traditional Hosting**: Static export option available

## Contributing

1. Follow the established code style and structure
2. Add TypeScript types for all new code
3. Write tests for new components and features
4. Update documentation as needed
5. Use semantic commit messages

## Browser Support

- **Chrome**: Latest 2 versions
- **Firefox**: Latest 2 versions
- **Safari**: Latest 2 versions
- **Edge**: Latest 2 versions

## License

This project is licensed under the MIT License - see the LICENSE file for details.
