import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.catalog_service import get_ingredient_options
from src.services.matcher import match_recipe
from src.services.storage_service import list_recipes


STATUS_LABELS = {
    "excellent": "🟢 很适合做",
    "good": "🟢 可以做",
    "substitution": "🟡 可以做，需要替换食材",
    "compromise": "🟠 可以做，但味道会有变化",
    "missing_required": "🔴 缺少必要食材",
}

QUALITY_LABELS = {
    "close": "基本没问题",
    "acceptable": "味道会有一点区别",
    "noticeable_difference": "味道会明显变化",
}


st.set_page_config(
    page_title="小猫食堂",
    page_icon="🐱",
    layout="wide",
)

recipes = list_recipes()
ingredient_options = get_ingredient_options()

st.title("🐱 小猫食堂")
st.caption("今天想吃点什么？")

if not recipes:
    st.info("还没有菜谱。先去“黄师傅后台”录入第一道菜吧。")
    st.stop()

tab_recipes, tab_ingredients = st.tabs(["📖 所有菜谱", "🥬 我有什么"])

with tab_recipes:
    cuisine_options = ["全部"] + sorted({recipe.cuisine for recipe in recipes})

    f1, f2, f3 = st.columns(3)
    with f1:
        cuisine = st.selectbox("菜系", cuisine_options)
    with f2:
        max_difficulty = st.slider("最高制作难度", 1, 5, 5)
    with f3:
        sort_by = st.selectbox(
            "排序",
            ["最简单", "食材最少", "最适合分享", "用时最短"],
        )

    filtered = [
        recipe
        for recipe in recipes
        if (cuisine == "全部" or recipe.cuisine == cuisine)
        and recipe.difficulty <= max_difficulty
    ]

    if sort_by == "最简单":
        filtered.sort(key=lambda r: (r.difficulty, r.time_minutes))
    elif sort_by == "食材最少":
        filtered.sort(key=lambda r: (r.ingredient_complexity, len(r.ingredients)))
    elif sort_by == "最适合分享":
        filtered.sort(key=lambda r: (-r.shareability, r.difficulty))
    else:
        filtered.sort(key=lambda r: r.time_minutes)

    for recipe in filtered:
        with st.expander(
            f"{recipe.name} · {recipe.time_minutes}分钟 · 难度 {'★' * recipe.difficulty}"
        ):
            c1, c2 = st.columns([1, 2])

            with c1:
                if recipe.image:
                    image_path = ROOT / recipe.image
                    if image_path.exists():
                        st.image(image_path, use_container_width=True)

                st.write(f"**菜系：** {recipe.cuisine}")
                st.write(f"**份数：** {recipe.servings}")
                st.write(f"**适合分享度：** {'★' * recipe.shareability}")

                if recipe.scenarios:
                    st.write("**适用场景：** " + " · ".join(recipe.scenarios))

            with c2:
                st.markdown("#### 食材")
                for ingredient in recipe.ingredients:
                    importance = {
                        "required": "必须",
                        "recommended": "推荐",
                        "optional": "可选",
                    }[ingredient.importance]

                    st.write(
                        f"- **{ingredient.name}** {ingredient.amount} · {importance}"
                    )

                    for substitute in ingredient.substitutes:
                        st.caption(
                            f"  ↳ 可用 {substitute.name} 替代："
                            f"{QUALITY_LABELS[substitute.quality]}"
                            + (f"；{substitute.note}" if substitute.note else "")
                        )

                st.markdown("#### 做法")
                for index, step in enumerate(recipe.steps, start=1):
                    st.write(f"{index}. {step}")

                if recipe.tips:
                    st.markdown("#### 🐱 黄师傅提醒")
                    for tip in recipe.tips:
                        st.write(f"- {tip}")

with tab_ingredients:
    selected = st.multiselect(
        "选择你现在有的食材",
        options=ingredient_options,
        placeholder="可以搜索鸡蛋、土豆、牛奶……",
    )

    if not selected:
        st.info("选几个家里现有的食材，我会告诉你哪些菜能直接做、哪些能替换后做。")
    else:
        results = [
            (recipe, match_recipe(recipe, selected))
            for recipe in recipes
        ]
        results.sort(
            key=lambda item: (
                not item[1]["cookable"],
                -item[1]["score"],
                item[0].difficulty,
            )
        )

        for recipe, match in results:
            with st.container(border=True):
                st.subheader(recipe.name)
                st.write(
                    f"{STATUS_LABELS[match['status']]} · 匹配度 {match['score']}/100"
                )

                if match["substitutions"]:
                    for substitution in match["substitutions"]:
                        st.write(
                            f"🔄 {substitution['original']} → "
                            f"**{substitution['substitute']}**"
                            f"（{QUALITY_LABELS[substitution['quality']]}）"
                        )
                        if substitution["note"]:
                            st.caption(substitution["note"])

                if match["missing_required"]:
                    st.write(
                        "🛒 缺关键食材："
                        + "、".join(match["missing_required"])
                    )

                if match["missing_recommended"]:
                    st.caption(
                        "最好再有："
                        + "、".join(match["missing_recommended"])
                    )
