import { expect, test } from "@playwright/test";

async function expectNoHorizontalOverflow(page) {
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth + 1,
      ),
    )
    .toBe(true);
}

test("landing page renders the WebGL bubbles without overflow", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");

  const canvas = page.getByTestId("interactive-background").locator("canvas");
  await expect(canvas).toBeVisible();
  const healthyWebGlContext = await canvas.evaluate((element) => {
    const context = element.getContext("webgl2") || element.getContext("webgl");
    return Boolean(
      context &&
      element.width > 0 &&
      element.height > 0 &&
      !context.isContextLost(),
    );
  });
  expect(healthyWebGlContext).toBe(true);
  await expectNoHorizontalOverflow(page);
  expect(errors).toEqual([]);
});

test("all analytics tabs stay inside their cards and viewport", async ({
  page,
}) => {
  await page.goto("/dashboard/analytics");
  await expect(
    page.getByRole("heading", { name: "Recruitment & Submission Analytics" }),
  ).toBeVisible();

  for (const viewport of [
    { width: 1478, height: 1000 },
    { width: 1280, height: 800 },
  ]) {
    await page.setViewportSize(viewport);
    for (const tab of [
      "Run Overview",
      "Candidate Quality",
      "Cost & Hireability",
    ]) {
      await page.getByRole("button", { name: tab }).click();
      await expect(page.locator(".recharts-wrapper").first()).toBeVisible();
      await expectNoHorizontalOverflow(page);
      const chartsContained = await page
        .locator(".recharts-wrapper")
        .evaluateAll((charts) =>
          charts.every((chart) => {
            const chartBox = chart.getBoundingClientRect();
            const cardBox = chart.closest("section")?.getBoundingClientRect();
            return (
              cardBox &&
              chartBox.width >= 100 &&
              chartBox.height >= 100 &&
              chartBox.left >= cardBox.left - 1 &&
              chartBox.right <= cardBox.right + 1
            );
          }),
        );
      expect(chartsContained).toBe(true);

      const visibleChartMarks = await page
        .locator(
          ".recharts-sector, .recharts-line-curve, .recharts-bar-rectangle path",
        )
        .count();
      expect(visibleChartMarks).toBeGreaterThan(0);
    }
  }

  await page.getByRole("button", { name: "Hackathon Readiness" }).click();
  await expect(
    page.getByText(/Valid Git history detected; private GitHub remote/),
  ).toBeVisible();
  await expect(
    page.getByText(/not currently a valid Git repository/),
  ).toHaveCount(0);
  await expectNoHorizontalOverflow(page);
});

test("pipeline columns are fully contained by the viewport", async ({
  page,
}) => {
  await page.goto("/dashboard/pipeline");
  await expect(
    page.getByRole("heading", { name: "Recruitment Pipeline" }),
  ).toBeVisible();
  await expect(page.getByText("Shortlisted", { exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  for (const viewport of [
    { width: 1478, height: 1000 },
    { width: 1280, height: 800 },
  ]) {
    await page.setViewportSize(viewport);
    await expectNoHorizontalOverflow(page);
    const columnsContained = await page
      .locator("main section")
      .evaluateAll((sections) =>
        sections.every((section) => {
          const box = section.getBoundingClientRect();
          return box.left >= 0 && box.right <= window.innerWidth + 1;
        }),
      );
    expect(columnsContained).toBe(true);
  }
});
