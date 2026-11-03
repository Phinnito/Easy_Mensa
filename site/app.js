const state = {
  recipes: [],
  knowledge: [],
  selectedIngredients: new Set(),
  selectedScenario: "",
};

const statusLabels = {
  excellent: "🟢 很适合做",
  good: "🟢 可以做",
  substitution: "🟡 可以做，需要替换食材",
  compromise: "🟠 可以做，但味道会有变化",
  missing_required: "🔴 缺少必要食材",
};

const qualityLabels = {
  close: "基本没问题",
  acceptable: "味道会有一点区别",
  noticeable_difference: "味道会明显变化",
};

const importanceLabels = {
  required: "必须",
  recommended: "推荐",
  optional: "可选",
};

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function normalize(value) {
  return String(value ?? "").trim().toLocaleLowerCase();
}



function findKnowledgeForIngredient(name) {
  const target = normalize(name);
  return state.knowledge.find(item =>
    normalize(item.ingredient) === target ||
    (item.aliases || []).some(alias => normalize(alias) === target)
  ) || null;
}

function relatedRecipesForIngredient(name) {
  const target = normalize(name);

  return state.recipes.filter(recipe =>
    (recipe.ingredients || []).some(ingredient =>
      normalize(ingredient.name) === target ||
      (ingredient.substitutes || []).some(sub => normalize(sub.name) === target)
    )
  );
}

function knowledgeCardMarkup(item) {
  const aliases = (item.aliases || []).length
    ? '<div class="knowledge-aliases">也叫：' + (item.aliases || []).map(esc).join(" · ") + '</div>'
    : "";

  return (
    '<article class="knowledge-card" data-knowledge-id="' + esc(item.id) + '">' +
      '<div class="knowledge-icon">🥬</div>' +
      '<div>' +
        '<h3>' + esc(item.ingredient) + '</h3>' +
        aliases +
        '<p>' + esc(item.summary || "黄师傅已经给这个食材写了小课堂。") + '</p>' +
      '</div>' +
    '</article>'
  );
}

function bindKnowledgeCards(container) {
  container.querySelectorAll(".knowledge-card").forEach(card => {
    card.addEventListener("click", () => openKnowledge(card.dataset.knowledgeId));
  });
}

function renderKnowledge() {
  const grid = document.getElementById("knowledge-grid");
  if (!grid) return;

  const query = normalize(document.getElementById("knowledge-search").value);
  const items = state.knowledge
    .filter(item => {
      const haystack = [
        item.ingredient,
        ...(item.aliases || []),
        item.summary,
        item.function,
        item.how_to_use,
      ].map(normalize).join(" ");
      return !query || haystack.includes(query);
    })
    .sort((a, b) => a.ingredient.localeCompare(b.ingredient, "zh-CN"));

  grid.innerHTML = items.length
    ? items.map(knowledgeCardMarkup).join("")
    : '<div class="empty">这里还没有对应的小课堂 📚</div>';

  bindKnowledgeCards(grid);
}


function imageMarkup(recipe) {
  if (!recipe.image) {
    return '<div class="recipe-placeholder">🍳</div>';
  }
  const relative = recipe.image.replace(/^images\//, "./images/");
  return '<img class="recipe-image" src="' + esc(relative) + '" alt="' + esc(recipe.name) + '">';
}

function cardMarkup(recipe, match = null) {
  const scenarios = (recipe.scenarios || [])
    .map(item => '<span class="chip">' + esc(item) + '</span>')
    .join("");

  const status = match
    ? '<div class="status ' + match.status + '">' + statusLabels[match.status] +
      ' · 匹配度 ' + match.score + '/100</div>'
    : "";

  return (
    '<article class="recipe-card" data-recipe-id="' + esc(recipe.id) + '">' +
      imageMarkup(recipe) +
      '<div class="recipe-body">' +
        '<h3>' + esc(recipe.name) + '</h3>' +
        '<div class="meta">' +
          esc(recipe.cuisine) + ' · ' + recipe.time_minutes + ' 分钟 · ' +
          recipe.servings + ' 人份<br>' +
          '难度 ' + "★".repeat(recipe.difficulty) +
        '</div>' +
        '<div class="chips">' + scenarios + '</div>' +
        status +
      '</div>' +
    '</article>'
  );
}

function bindRecipeCards(container) {
  container.querySelectorAll(".recipe-card").forEach(card => {
    card.addEventListener("click", () => openRecipe(card.dataset.recipeId));
  });
}

function renderRecipes() {
  const grid = document.getElementById("recipe-grid");
  const query = normalize(document.getElementById("search").value);
  const cuisine = document.getElementById("cuisine-filter").value;

  const recipes = state.recipes.filter(recipe => {
    const haystack = [
      recipe.name,
      recipe.cuisine,
      ...(recipe.ingredients || []).map(item => item.name),
    ].map(normalize).join(" ");

    return (!query || haystack.includes(query)) &&
      (!cuisine || recipe.cuisine === cuisine);
  });

  grid.innerHTML = recipes.length
    ? recipes.map(recipe => cardMarkup(recipe)).join("")
    : '<div class="empty">没有找到匹配的菜单 🐱</div>';

  bindRecipeCards(grid);
}

function collectIngredients() {
  const counts = new Map();

  state.recipes.forEach(recipe => {
    (recipe.ingredients || []).forEach(ingredient => {
      const names = [
        ingredient.name,
        ...(ingredient.substitutes || []).map(item => item.name),
      ];

      names.forEach(name => {
        if (!name) return;
        counts.set(name, (counts.get(name) || 0) + 1);
      });
    });
  });

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "zh-CN"))
    .map(([name]) => name);
}

function renderIngredientCloud() {
  const root = document.getElementById("ingredient-cloud");
  const query = normalize(document.getElementById("ingredient-search").value);

  const ingredients = collectIngredients().filter(name =>
    !query || normalize(name).includes(query)
  );

  root.innerHTML = ingredients.map(name => {
    const selected = state.selectedIngredients.has(name) ? " selected" : "";
    return '<button class="ingredient-button' + selected + '" data-name="' +
      esc(name) + '">' + esc(name) + '</button>';
  }).join("");

  root.querySelectorAll(".ingredient-button").forEach(button => {
    button.addEventListener("click", () => {
      const name = button.dataset.name;
      if (state.selectedIngredients.has(name)) {
        state.selectedIngredients.delete(name);
      } else {
        state.selectedIngredients.add(name);
      }
      renderIngredientCloud();
      renderMatches();
    });
  });

  const summary = document.getElementById("selected-summary");
  summary.textContent = state.selectedIngredients.size
    ? [...state.selectedIngredients].join("、")
    : "还没有选择食材";
}

function matchRecipe(recipe) {
  const available = new Set([...state.selectedIngredients].map(normalize));
  const missingRequired = [];
  const missingRecommended = [];
  const substitutions = [];

  const qualityRank = {
    close: 0,
    acceptable: 1,
    noticeable_difference: 2,
  };

  (recipe.ingredients || []).forEach(ingredient => {
    if (available.has(normalize(ingredient.name))) return;

    const matches = (ingredient.substitutes || [])
      .filter(item => available.has(normalize(item.name)))
      .sort((a, b) => qualityRank[a.quality] - qualityRank[b.quality]);

    if (matches.length) {
      substitutions.push({
        original: ingredient.name,
        substitute: matches[0].name,
        quality: matches[0].quality,
        note: matches[0].note || "",
      });
      return;
    }

    if (ingredient.importance === "required") {
      missingRequired.push(ingredient.name);
    } else if (ingredient.importance === "recommended") {
      missingRecommended.push(ingredient.name);
    }
  });

  let status = "excellent";
  if (missingRequired.length) status = "missing_required";
  else if (substitutions.some(item => item.quality === "noticeable_difference")) status = "compromise";
  else if (substitutions.length) status = "substitution";
  else if (missingRecommended.length) status = "good";

  const penalty =
    missingRequired.length * 40 +
    missingRecommended.length * 7 +
    substitutions.reduce((sum, item) => {
      return sum + { close: 2, acceptable: 7, noticeable_difference: 15 }[item.quality];
    }, 0);

  return {
    status,
    cookable: !missingRequired.length,
    score: Math.max(0, 100 - penalty),
    missingRequired,
    missingRecommended,
    substitutions,
  };
}

function renderMatches() {
  const grid = document.getElementById("match-grid");

  if (!state.selectedIngredients.size) {
    grid.innerHTML = '<div class="empty">先选几个家里现有的食材 🥬</div>';
    return;
  }

  const results = state.recipes
    .map(recipe => ({ recipe, match: matchRecipe(recipe) }))
    .sort((a, b) => {
      if (a.match.cookable !== b.match.cookable) return a.match.cookable ? -1 : 1;
      return b.match.score - a.match.score || a.recipe.difficulty - b.recipe.difficulty;
    });

  grid.innerHTML = results.map(item => cardMarkup(item.recipe, item.match)).join("");
  bindRecipeCards(grid);
}

function openRecipe(recipeId) {
  const recipe = state.recipes.find(item => item.id === recipeId);
  if (!recipe) return;

  const ingredients = (recipe.ingredients || []).map(ingredient => {
    const ingredientKnowledge = findKnowledgeForIngredient(ingredient.name);
    const ingredientName = ingredientKnowledge
      ? '<button class="knowledge-inline" data-knowledge-id="' + esc(ingredientKnowledge.id) + '">' +
        esc(ingredient.name) + ' 📚</button>'
      : '<strong>' + esc(ingredient.name) + '</strong>';

    const subs = (ingredient.substitutes || []).map(sub => {
      const subKnowledge = findKnowledgeForIngredient(sub.name);
      const subName = subKnowledge
        ? '<button class="knowledge-inline" data-knowledge-id="' + esc(subKnowledge.id) + '">' +
          esc(sub.name) + ' 📚</button>'
        : esc(sub.name);

      return '<div class="substitute">↳ 可用 ' + subName + ' 替代 · ' +
        esc(qualityLabels[sub.quality]) +
        (sub.note ? ' · ' + esc(sub.note) : '') +
        '</div>';
    }).join("");

    return '<div class="ingredient-line">' + ingredientName + ' ' +
      esc(ingredient.amount || "") + ' · ' + esc(importanceLabels[ingredient.importance]) +
      subs + '</div>';
  }).join("");

  const steps = (recipe.steps || []).map((step, index) =>
    '<div class="step"><span class="step-number">' + (index + 1) +
    '</span><div>' + esc(step) + '</div></div>'
  ).join("");

  const tips = (recipe.tips || []).length
    ? '<h3>🐱 黄师傅提醒</h3><ul>' +
      recipe.tips.map(tip => '<li>' + esc(tip) + '</li>').join("") +
      '</ul>'
    : "";

  document.getElementById("dialog-content").innerHTML =
    '<div class="dialog-inner">' +
      '<h2>' + esc(recipe.name) + '</h2>' +
      '<div class="meta">' + esc(recipe.cuisine) + ' · ' +
      recipe.time_minutes + ' 分钟 · ' + recipe.servings + ' 人份 · 难度 ' +
      "★".repeat(recipe.difficulty) + '</div>' +
      '<h3>🥬 食材</h3>' + ingredients +
      '<h3>🍳 做法</h3>' + steps +
      tips +
    '</div>';

  const dialog = document.getElementById("recipe-dialog");
  if (!dialog.open) dialog.showModal();

  dialog.querySelectorAll(".knowledge-inline").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation();
      openKnowledge(button.dataset.knowledgeId);
    });
  });
}

function openKnowledge(knowledgeId) {
  const item = state.knowledge.find(entry => entry.id === knowledgeId);
  if (!item) return;

  const section = (title, body) => body
    ? '<section class="knowledge-section"><h3>' + title + '</h3><p>' + esc(body) + '</p></section>'
    : "";

  const mistakes = (item.mistakes || []).length
    ? '<section class="knowledge-section"><h3>⚠️ 常见错误</h3><ul>' +
      item.mistakes.map(value => '<li>' + esc(value) + '</li>').join("") +
      '</ul></section>'
    : "";

  const tips = (item.tips || []).length
    ? '<section class="knowledge-section"><h3>🐯 黄师傅提醒</h3><ul>' +
      item.tips.map(value => '<li>' + esc(value) + '</li>').join("") +
      '</ul></section>'
    : "";

  const aliases = (item.aliases || []).length
    ? '<div class="knowledge-aliases">也叫：' + item.aliases.map(esc).join(" · ") + '</div>'
    : "";

  const related = relatedRecipesForIngredient(item.ingredient);
  const relatedMarkup = related.length
    ? '<section class="knowledge-section"><h3>🍽️ 用到它的菜</h3><div class="related-recipes">' +
      related.map(recipe =>
        '<button class="related-recipe-button" data-recipe-id="' + esc(recipe.id) + '">' +
        esc(recipe.name) + '</button>'
      ).join("") +
      '</div></section>'
    : "";

  const content = document.getElementById("dialog-content");
  content.innerHTML =
    '<div class="dialog-inner knowledge-detail">' +
      '<div class="knowledge-detail-icon">🥬</div>' +
      '<h2>' + esc(item.ingredient) + '</h2>' +
      aliases +
      (item.summary ? '<p class="knowledge-summary">' + esc(item.summary) + '</p>' : '') +
      section("它在做饭里是干什么的？", item.function) +
      section("🍳 怎么使用？", item.how_to_use) +
      section("🛒 买的时候怎么看？", item.how_to_choose) +
      section("🧊 怎么保存？", item.storage) +
      mistakes +
      tips +
      relatedMarkup +
    '</div>';

  const dialog = document.getElementById("recipe-dialog");
  if (!dialog.open) dialog.showModal();

  dialog.querySelectorAll(".related-recipe-button").forEach(button => {
    button.addEventListener("click", () => openRecipe(button.dataset.recipeId));
  });
}

function renderScenarios() {
  const root = document.getElementById("scenario-pills");
  const scenarios = [...new Set(
    state.recipes.flatMap(recipe => recipe.scenarios || [])
  )];

  root.innerHTML = scenarios.map(scenario => {
    const selected = state.selectedScenario === scenario ? " selected" : "";
    return '<button class="scenario-button' + selected + '" data-scenario="' +
      esc(scenario) + '">' + esc(scenario) + '</button>';
  }).join("");

  root.querySelectorAll(".scenario-button").forEach(button => {
    button.addEventListener("click", () => {
      state.selectedScenario =
        state.selectedScenario === button.dataset.scenario ? "" : button.dataset.scenario;
      renderScenarios();
    });
  });
}

function rollRecipe() {
  const pool = state.recipes.filter(recipe =>
    !state.selectedScenario || (recipe.scenarios || []).includes(state.selectedScenario)
  );

  const target = document.getElementById("roll-result");
  if (!pool.length) {
    target.innerHTML = '<div class="empty">这个场景还没有菜单。</div>';
    return;
  }

  const recipe = pool[Math.floor(Math.random() * pool.length)];
  target.innerHTML = cardMarkup(recipe);
  bindRecipeCards(target);
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(item => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach(view => view.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(tab.dataset.view + "-view").classList.add("active");
    });
  });
}

async function init() {
  setupTabs();

  const [recipeResponse, knowledgeResponse] = await Promise.all([
    fetch("./recipes.json", { cache: "no-store" }),
    fetch("./knowledge.json", { cache: "no-store" }),
  ]);

  state.recipes = recipeResponse.ok ? await recipeResponse.json() : [];
  state.knowledge = knowledgeResponse.ok ? await knowledgeResponse.json() : [];

  const cuisines = [...new Set(state.recipes.map(recipe => recipe.cuisine))].sort();
  const cuisineSelect = document.getElementById("cuisine-filter");

  cuisines.forEach(cuisine => {
    const option = document.createElement("option");
    option.value = cuisine;
    option.textContent = cuisine;
    cuisineSelect.appendChild(option);
  });

  document.getElementById("search").addEventListener("input", renderRecipes);
  cuisineSelect.addEventListener("change", renderRecipes);
  document.getElementById("ingredient-search").addEventListener("input", renderIngredientCloud);
  document.getElementById("knowledge-search").addEventListener("input", renderKnowledge);

  document.getElementById("clear-pantry").addEventListener("click", () => {
    state.selectedIngredients.clear();
    renderIngredientCloud();
    renderMatches();
  });

  document.getElementById("roll-button").addEventListener("click", rollRecipe);

  document.getElementById("dialog-close").addEventListener("click", () => {
    document.getElementById("recipe-dialog").close();
  });

  renderRecipes();
  renderIngredientCloud();
  renderMatches();
  renderScenarios();
  renderKnowledge();
}

init().catch(error => {
  console.error(error);
  document.getElementById("recipe-grid").innerHTML =
    '<div class="empty">菜单加载失败，请稍后刷新。</div>';
});
