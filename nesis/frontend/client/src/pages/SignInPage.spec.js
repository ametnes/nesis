import { test, expect } from '@playwright/experimental-ct-react';
import SignInPage from './SignInPage';

// test.use({ viewport: { width: 1024, height: 768 } });

test.describe('SignInPage Component Test', () => {
  test('should display the Nesis logo with correct dimensions', async ({
    mount,
  }) => {
    const component = await mount(<SignInPage />);
    const logo = component.locator('img[alt="Nesis Logo"]');
    await expect(logo).toBeVisible();
    const box = await logo.boundingBox();
    await expect(box.width).toBeCloseTo(200, 1); // Checking if width is 200px
    await expect(box.height).toBeCloseTo(200, 1); // Checking if height is 200px
  });

  test('should display the main headings', async ({ mount }) => {
    const component = await mount(<SignInPage />);
    const heading1 = component.locator('h1');
    await expect(heading1).toHaveText('Nesis');
    const heading2 = component.locator('h2');
    await expect(heading2).toHaveText('Your Enterprise Knowledge Partner');
  });

  test('should render the email and password fields with the right placeholders', async ({
    mount,
  }) => {
    const component = await mount(<SignInPage />);
    const emailField = component.locator('input[name="email"]');
    await expect(emailField).toBeVisible();
    await expect(emailField).toHaveAttribute('placeholder', 'enter your email');
    const passwordField = component.locator('input[name="password"]');
    await expect(passwordField).toBeVisible();
    await expect(passwordField).toHaveAttribute('placeholder', '**********');
  });

  test('should render the Log In button', async ({ mount }) => {
    const component = await mount(<SignInPage />);
    const loginButton = component.locator('button[type="submit"]');
    await expect(loginButton).toBeVisible();
    await expect(loginButton).toHaveText('Log In');
  });

  test('should render the Azure button if oauth is enabled', async ({
    mount,
  }) => {
    const component = await mount(<SignInPage testazureAuthEnabled={true} />);
    const azureButton = component.locator(
      'button:has-text("Sign in with Microsoft")',
    );
    await expect(azureButton).toBeVisible();
  });

  test('should toggle between password and Azure login', async ({ mount }) => {
    const component = await mount(<SignInPage testazureAuthEnabled={true} />);
    const toggleButton = component.locator('span:has-text("Use password")');
    await expect(toggleButton).toBeVisible();
    await toggleButton.click();
    const toggleButton2 = component.locator('span:has-text("Use Azure")');
    await expect(toggleButton2).toBeVisible();
    await toggleButton2.click();
    await expect(toggleButton).toBeVisible();
  });
});

//these are run when the server is live

// test.describe('SignInPage E2E Test', () => {
//   // test.beforeEach(async ({ page }) => {
//   //   await page.goto('http://localhost:58000/signin');
//   // });

//   test('shows error message on incorrect email or password', async ({
//     page,
//   }) => {
//     await page.goto('http://localhost:58000/signin');
//     // Mock the API response to return 401 Unauthorized
//     // await page.route('**/sessions', (route) =>
//     //   route.fulfill({
//     //     status: 401,
//     //     body: JSON.stringify({ message: 'Incorrect email or password' }),
//     //   }),
//     // );

//     await page.fill('input[name="email"]', 'incorrect@example.com');
//     await page.fill('input[name="password"]', 'wrongpassword');
//     await page.click('button[type="submit"]');

//     await expect(
//       page.locator('text=Incorrect email or password'),
//     ).toBeVisible();
//   });

//   test('navigates to the discovery page on successful login', async ({
//     page,
//   }) => {
//     await page.goto('http://localhost:58000/signin');
//     // Mock the API response to return a successful login if needed
//     // await page.route('**/sessions', (route) =>
//     //   route.fulfill({
//     //     status: 200,
//     //     body: JSON.stringify({ token: 'fake-token' }),
//     //   }),
//     // );

//     const emailField = page.locator('input[name="email"]');
//     await expect(emailField).toBeVisible();
//     await emailField.fill('some.email@domain.com');

//     const passwordField = page.locator('input[name="password"]');
//     await expect(passwordField).toBeVisible();
//     await passwordField.fill('password'); // Replace 'your_password' with the actual password

//     const loginButton = page.locator('button[type="submit"]');
//     await expect(loginButton).toBeVisible();
//     await loginButton.click();

//     await expect(page.locator('text=Chat with your Documents')).toBeVisible();
//   });
// });
