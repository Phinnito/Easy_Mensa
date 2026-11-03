import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.recipe import Ingredient, Recipe, Substitute
from src.services.catalog_service import get_ingredient_options
from src.services.git_service import publish_changes
from src.services.storage_service import save_recipe, save_recipe_image


CUISINES = [
    "中餐",
    "西餐",
    "南美菜",
    "东亚菜",
    "东南亚菜",
    "南亚菜",
    "非洲菜",
]

SCENARIOS = [
    "聚会菜谱",
    "精致一人食",
    "随便吃点",
    "两个人吃",
    "认真做饭",
]

IMPORTANCE_LABELS = {
    "必须有": "required",
    "最好有": "recommended",
    "有更好": "optional",
}

QUALITY_LABELS = {
    "基本没问题": "close",
    "味道会有一点区别": "acceptable",
    "味道会明显变化": "noticeable_difference",
}


st.set_page_config(
    page_title="黄师傅后台",
    page_icon="👨‍🍳",
    layout="wide",
)


def ensure_state() -> None:
    st.session_state.setdefault("ingredient_rows", 2)
    st.session_state.setdefault("step_rows", 3)
    st.session_state.setdefault("tip_rows", 1)
    st.session_state.setdefault("substitute_rows", {})


def reset_editor() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith(("ingredient_", "sub_", "step_", "tip_", "recipe_")):
            del st.session_state[key]

    st.session_state["ingredient_rows"] = 2
    st.session_state["step_rows"] = 3
    st.session_state["tip_rows"] = 1
    st.session_state["substitute_rows"] = {}


def ingredient_selector(label: str, key: str, options: list[str]):
    return st.selectbox(
        label,
        options=options,
        index=None,
        placeholder="搜索已有食材，或直接输入新的",
        accept_new_options=True,
        filter_mode="fuzzy",
        key=key,
    )


ensure_state()
known_ingredients = get_ingredient_options()

st.title("👨‍🍳 黄师傅后台")
st.caption("这里负责把菜谱变成结构化数据。以前录过的食材会自动成为快捷选项。")

tab_new, tab_help = st.tabs(["➕ 新增菜谱", "📚 数据规则"])

with tab_new:
    left, right = st.columns([1.6, 1])

    with left:
        st.subheader("基本信息")

        recipe_name = st.text_input(
            "菜名",
            placeholder="例如：辣椒炒肉",
            key="recipe_name",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            cuisine = st.selectbox("菜系", CUISINES, key="recipe_cuisine")
        with c2:
            time_minutes = st.number_input(
                "时间（分钟）",
                min_value=1,
                value=25,
                step=5,
                key="recipe_time",
            )
        with c3:
            servings = st.number_input(
                "份数",
                min_value=1,
                value=2,
                step=1,
                key="recipe_servings",
            )

        st.write("适用场景")
        scenarios = st.pills(
            "适用场景",
            SCENARIOS,
            selection_mode="multi",
            label_visibility="collapsed",
            key="recipe_scenarios",
        )

        st.subheader("评分")
        r1, r2, r3 = st.columns(3)
        with r1:
            difficulty = st.slider("制作难度", 1, 5, 2, key="recipe_difficulty")
        with r2:
            ingredient_complexity = st.slider(
                "食材复杂度",
                1,
                5,
                2,
                key="recipe_complexity",
            )
        with r3:
            shareability = st.slider(
                "适合分享度",
                1,
                5,
                3,
                key="recipe_shareability",
            )

    with right:
        st.subheader("菜品图片")
        image_file = st.file_uploader(
            "上传一张照片（可选）",
            type=["png", "jpg", "jpeg", "webp"],
            key="recipe_image",
        )
        if image_file is not None:
            st.image(image_file, caption="预览", use_container_width=True)

        st.info(
            "以后添加过的主食材和替换食材都会进入全局候选库，"
            "下一道菜就可以直接搜索选择。"
        )

    st.divider()
    st.subheader("🥬 食材")

    ingredients: list[Ingredient] = []

    for i in range(st.session_state["ingredient_rows"]):
        with st.container(border=True):
            top1, top2, top3 = st.columns([2, 1, 1.2])

            with top1:
                name = ingredient_selector(
                    f"食材 {i + 1}",
                    f"ingredient_name_{i}",
                    known_ingredients,
                )

            with top2:
                amount = st.text_input(
                    "用量",
                    placeholder="250g / 2个 / 适量",
                    key=f"ingredient_amount_{i}",
                )

            with top3:
                importance_label = st.selectbox(
                    "重要程度",
                    list(IMPORTANCE_LABELS),
                    key=f"ingredient_importance_{i}",
                )

            sub_count = st.session_state["substitute_rows"].get(i, 0)

            if sub_count:
                st.caption("可替换食材")

            substitutes: list[Substitute] = []

            for j in range(sub_count):
                s1, s2 = st.columns([1.5, 1.5])
                with s1:
                    sub_name = ingredient_selector(
                        f"替换食材 {j + 1}",
                        f"sub_name_{i}_{j}",
                        known_ingredients,
                    )
                with s2:
                    quality_label = st.selectbox(
                        "替换后的影响",
                        list(QUALITY_LABELS),
                        key=f"sub_quality_{i}_{j}",
                    )

                note = st.text_input(
                    "替换说明（可选）",
                    placeholder="例如：可以正常做，但椰香会变弱",
                    key=f"sub_note_{i}_{j}",
                )

                if sub_name:
                    substitutes.append(
                        Substitute(
                            name=sub_name.strip(),
                            quality=QUALITY_LABELS[quality_label],
                            note=note.strip(),
                        )
                    )

            b1, b2, _ = st.columns([1, 1, 3])
            with b1:
                if st.button(
                    "＋ 替换食材",
                    key=f"add_substitute_{i}",
                    use_container_width=True,
                ):
                    st.session_state["substitute_rows"][i] = sub_count + 1
                    st.rerun()

            with b2:
                if sub_count and st.button(
                    "－ 删除替换",
                    key=f"remove_substitute_{i}",
                    use_container_width=True,
                ):
                    st.session_state["substitute_rows"][i] = sub_count - 1
                    st.rerun()

            if name:
                ingredients.append(
                    Ingredient(
                        name=name.strip(),
                        amount=amount.strip(),
                        importance=IMPORTANCE_LABELS[importance_label],
                        substitutes=substitutes,
                    )
                )

    add_col, remove_col, _ = st.columns([1, 1, 3])
    with add_col:
        if st.button("＋ 添加食材", use_container_width=True):
            st.session_state["ingredient_rows"] += 1
            st.rerun()

    with remove_col:
        if (
            st.session_state["ingredient_rows"] > 1
            and st.button("－ 删除最后一项", use_container_width=True)
        ):
            last_index = st.session_state["ingredient_rows"] - 1
            st.session_state["substitute_rows"].pop(last_index, None)
            st.session_state["ingredient_rows"] -= 1
            st.rerun()

    st.divider()
    st.subheader("🍳 制作步骤")

    steps: list[str] = []
    for i in range(st.session_state["step_rows"]):
        value = st.text_area(
            f"步骤 {i + 1}",
            height=70,
            placeholder="写清楚这一小步要做什么",
            key=f"step_{i}",
        )
        if value.strip():
            steps.append(value.strip())

    sc1, sc2, _ = st.columns([1, 1, 3])
    with sc1:
        if st.button("＋ 添加步骤", use_container_width=True):
            st.session_state["step_rows"] += 1
            st.rerun()
    with sc2:
        if (
            st.session_state["step_rows"] > 1
            and st.button("－ 删除最后一步", use_container_width=True)
        ):
            st.session_state["step_rows"] -= 1
            st.rerun()

    st.subheader("🐱 黄师傅提醒")
    tips: list[str] = []

    for i in range(st.session_state["tip_rows"]):
        value = st.text_input(
            f"提醒 {i + 1}",
            placeholder="例如：辣椒不要炒得太软",
            key=f"tip_{i}",
        )
        if value.strip():
            tips.append(value.strip())

    tc1, tc2, _ = st.columns([1, 1, 3])
    with tc1:
        if st.button("＋ 添加提醒", use_container_width=True):
            st.session_state["tip_rows"] += 1
            st.rerun()
    with tc2:
        if (
            st.session_state["tip_rows"] > 1
            and st.button("－ 删除最后一条", use_container_width=True)
        ):
            st.session_state["tip_rows"] -= 1
            st.rerun()

    st.divider()

    publish = st.button(
        "🚀 保存并发布到小猫食堂",
        type="primary",
        use_container_width=True,
    )

    if publish:
        errors: list[str] = []

        if not recipe_name.strip():
            errors.append("请填写菜名。")
        if not ingredients:
            errors.append("至少需要一个食材。")
        if not steps:
            errors.append("至少需要一个制作步骤。")

        if errors:
            for error in errors:
                st.error(error)
        else:
            recipe_id = f"recipe-{uuid.uuid4().hex[:10]}"
            image_path = save_recipe_image(recipe_id, image_file)

            recipe = Recipe(
                id=recipe_id,
                name=recipe_name.strip(),
                cuisine=cuisine,
                difficulty=difficulty,
                ingredient_complexity=ingredient_complexity,
                shareability=shareability,
                time_minutes=int(time_minutes),
                servings=int(servings),
                scenarios=list(scenarios or []),
                image=image_path,
                ingredients=ingredients,
                steps=steps,
                tips=tips,
            )

            path = save_recipe(recipe)

            success, message = publish_changes(
                f"Add recipe: {recipe.name}"
            )

            if success:
                st.success(f"✅ {recipe.name} 已保存。{message}")
                st.caption(f"数据文件：{path.relative_to(ROOT)}")
                st.balloons()
            else:
                st.warning(
                    f"菜谱已经保存，但自动推送 GitHub 没成功：{message}"
                )
                st.caption("在 Codespaces 中通常可以直接自动发布；其他环境可手动 git push。")

with tab_help:
    st.markdown(
        """
        ### 食材重要程度
        - **必须有**：缺少并且没有可用替代时，这道菜会显示“缺关键食材”。
        - **最好有**：没有也能做，但系统会提醒。
        - **有更好**：完全可选。

        ### 替换后的影响
        - **基本没问题**：可视为很接近原方案。
        - **味道会有一点区别**：仍然推荐做，但会提示替换。
        - **味道会明显变化**：仍可做，但会明确标注风味偏差。

        原始食材和替换食材都会自动进入教学候选库。
        """
    )
