const {test,expect}=require('@playwright/test');
test('guest can inspect public architecture without authentication',async({page})=>{await page.goto('/#architecture');await expect(page.getByText('Interactive Architecture')).toBeVisible();await expect(page.getByText('Feature Store')).toBeVisible();});
test('demo mode is visibly read only',async({page})=>{await page.goto('/#demo');await expect(page.getByText(/read only/i)).toBeVisible();await expect(page.getByText(/paper trading disabled/i)).toBeVisible();});
