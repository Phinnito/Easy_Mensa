import sys
import uuid
from collections import Counter
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.recipe import Ingredient, Recipe, Substitute
from src.services.catalog_service import get_ingredient_options
from src.services.git_service import publish_changes
from src.services.storage_service import (
    delete_recipe,
    get_recipe,
    list_recipes,
    save_recipe,
    save_recipe_image,
)

CUISINES = ["中餐", "西餐", "南美菜", "东亚菜", "东南亚菜", "南亚菜", "非洲菜"]
SCENARIOS = ["聚会菜谱", "精致一人食", "随便吃点", "两个人吃", "认真做饭"]

IMPORTANCE_LABELS = {"必须有": "required", "最好有": "recommended", "有更好": "optional"}
IMPORTANCE_REVERSE = {value: key for key, value in IMPORTANCE_LABELS.items()}

QUALITY_LABELS = {
    "基本没问题": "close",
    "味道会有一点区别": "acceptable",
    "味道会明显变化": "noticeable_difference",
}
QUALITY_REVERSE = {value: key for key, value in QUALITY_LABELS.items()}

st.set_page_config(page_title="黄师傅后台", page_icon="👨‍🍳", layout="wide")


def init_state() -> None:
    st.session_state.setdefault("admin_page", "list")
    st.session_state.setdefault("selected_recipe_id", None)
    st.session_state.setdefault("editor_nonce", 0)
    st.session_state.setdefault("delete_pending", None)


def go(page: str) -> None:
    st.session_state["admin_page"] = page
    st.rerun()


def new_recipe() -> None:
    st.session_state["selected_recipe_id"] = None
    st.session_state["editor_nonce"] += 1
    st.session_state["admin_page"] = "editor"
    st.rerun()


def edit_recipe(recipe_id: str) -> None:
    st.session_state["selected_recipe_id"] = recipe_id
    st.session_state["editor_nonce"] += 1
    st.session_state["admin_page"] = "editor"
    st.rerun()


def unique_options(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def ingredient_selector(label, key, options, default=None):
    choices = unique_options(options + ([default] if default else []))
    index = choices.index(default) if default and default in choices else None
    return st.selectbox(
        label,
        choices,
        index=index,
        placeholder="搜索已有食材，或直接输入新的",
        accept_new_options=True,
        filter_mode="fuzzy",
        key=key,
    )


def sidebar() -> None:
    st.sidebar.title("👨‍🍳 黄师傅")
    st.sidebar.caption("小猫食堂 · 菜单管理")

    if st.sidebar.button("📋 菜单列表", use_container_width=True):
        go("list")
    if st.sidebar.button("➕ 新增菜单", use_container_width=True):
        new_recipe()
    if st.sidebar.button("📚 数据规则", use_container_width=True):
        go("help")


def recipe_list_page() -> None:
    recipes = list_recipes()
    st.title("📋 菜单列表")
    st.caption("查看、编辑或删除已经发布的菜单。")

    a, b = st.columns([3, 1])
    with a:
        search = st.text_input(
            "搜索菜单",
            placeholder="输入菜名，例如：麻婆豆腐",
            label_visibility="collapsed",
        )
    with b:
        if st.button("➕ 新增菜单", type="primary", use_container_width=True):
            new_recipe()

    if not recipes:
        st.info("还没有任何菜单。")
        return

    counts = Counter(recipe.name for recipe in recipes)
    duplicates = [f"{name} × {count}" for name, count in counts.items() if count > 1]
    if duplicates:
        st.warning("检测到重复菜名：" + "、".join(duplicates) + "。可以逐个确认后删除。")

    filtered = [
        recipe
        for recipe in recipes
        if not search.strip() or search.strip().casefold() in recipe.name.casefold()
    ]
    filtered.sort(key=lambda recipe: (recipe.name, recipe.id))
    st.caption(f"共 {len(recipes)} 个菜单")

    for recipe in filtered:
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 1, 1])

            with c1:
                suffix = " · ⚠️ 重复" if counts[recipe.name] > 1 else ""
                st.subheader(recipe.name + suffix)
                st.caption(
                    f"{recipe.cuisine} · {recipe.time_minutes} 分钟 · "
                    f"{recipe.servings} 人份 · 难度 {'★' * recipe.difficulty}"
                )
                if recipe.scenarios:
                    st.write(" · ".join(recipe.scenarios))
                st.caption(f"ID: {recipe.id}")

            with c2:
                if st.button("✏️ 编辑", key=f"edit_{recipe.id}", use_container_width=True):
                    edit_recipe(recipe.id)

            with c3:
                if st.button("🗑️ 删除", key=f"delete_{recipe.id}", use_container_width=True):
                    st.session_state["delete_pending"] = recipe.id
                    st.rerun()

            if st.session_state["delete_pending"] == recipe.id:
                st.error(
                    f"确定删除「{recipe.name}」吗？菜谱数据和这道菜对应的图片都会删除。"
                )
                d1, d2, _ = st.columns([1, 1, 3])

                with d1:
                    if st.button(
                        "确认删除",
                        key=f"confirm_{recipe.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        if delete_recipe(recipe.id):
                            success, message = publish_changes(f"Delete recipe: {recipe.name}")
                            if success:
                                st.session_state["delete_pending"] = None
                                st.success(f"已删除「{recipe.name}」。{message}")
                                st.rerun()
                            else:
                                st.warning(f"本地已删除，但同步 GitHub 失败：{message}")
                        else:
                            st.warning("这道菜已经不存在了。")

                with d2:
                    if st.button(
                        "取消",
                        key=f"cancel_{recipe.id}",
                        use_container_width=True,
                    ):
                        st.session_state["delete_pending"] = None
                        st.rerun()


def editor_page() -> None:
    selected_id = st.session_state["selected_recipe_id"]
    existing = get_recipe(selected_id) if selected_id else None
    editing = existing is not None

    if selected_id and not existing:
        st.error("找不到这道菜，可能已经被删除。")
        if st.button("返回菜单列表"):
            go("list")
        return

    token = f"{selected_id or 'new'}_{st.session_state['editor_nonce']}"
    known = get_ingredient_options()

    ingredient_count_key = f"ingredient_rows_{token}"
    step_count_key = f"step_rows_{token}"
    tip_count_key = f"tip_rows_{token}"

    st.session_state.setdefault(
        ingredient_count_key,
        max(1, len(existing.ingredients)) if existing else 2,
    )
    st.session_state.setdefault(
        step_count_key,
        max(1, len(existing.steps)) if existing else 3,
    )
    st.session_state.setdefault(
        tip_count_key,
        max(1, len(existing.tips)) if existing else 1,
    )

    st.title(f"✏️ 编辑菜单 · {existing.name}" if editing else "➕ 新增菜单")
    if editing:
        st.caption(f"菜单 ID：{existing.id}")

    if st.button("← 返回菜单列表"):
        go("list")

    left, right = st.columns([1.6, 1])

    with left:
        st.subheader("基本信息")
        recipe_name = st.text_input(
            "菜名",
            value=existing.name if existing else "",
            placeholder="例如：辣椒炒肉",
            key=f"name_{token}",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            cuisine_index = CUISINES.index(existing.cuisine) if existing else 0
            cuisine = st.selectbox(
                "菜系",
                CUISINES,
                index=cuisine_index,
                key=f"cuisine_{token}",
            )
        with c2:
            time_minutes = st.number_input(
                "时间（分钟）",
                min_value=1,
                value=existing.time_minutes if existing else 25,
                step=5,
                key=f"time_{token}",
            )
        with c3:
            servings = st.number_input(
                "份数",
                min_value=1,
                value=existing.servings if existing else 2,
                step=1,
                key=f"servings_{token}",
            )

        st.write("适用场景")
        scenarios = st.pills(
            "适用场景",
            SCENARIOS,
            selection_mode="multi",
            default=existing.scenarios if existing else [],
            label_visibility="collapsed",
            key=f"scenarios_{token}",
        )

        st.subheader("评分")
        r1, r2, r3 = st.columns(3)
        with r1:
            difficulty = st.slider(
                "制作难度", 1, 5, existing.difficulty if existing else 2, key=f"difficulty_{token}"
            )
        with r2:
            ingredient_complexity = st.slider(
                "食材复杂度",
                1,
                5,
                existing.ingredient_complexity if existing else 2,
                key=f"complexity_{token}",
            )
        with r3:
            shareability = st.slider(
                "适合分享度",
                1,
                5,
                existing.shareability if existing else 3,
                key=f"share_{token}",
            )

    with right:
        st.subheader("菜品图片")
        if existing and existing.image:
            path = ROOT / existing.image
            if path.exists():
                st.image(path, caption="当前图片", use_container_width=True)

        image_file = st.file_uploader(
            "上传新图片（可选）" if editing else "上传图片（可选）",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"image_{token}",
        )
        if image_file is not None:
            st.image(image_file, caption="新图片预览", use_container_width=True)

        st.info("编辑已有菜单时会保留原 ID，不会再生成一份重复菜单。")

    st.divider()
    st.subheader("🥬 食材")
    ingredients = []
    ingredient_count = st.session_state[ingredient_count_key]

    for i in range(ingredient_count):
        default_ing = existing.ingredients[i] if existing and i < len(existing.ingredients) else None
        sub_count_key = f"sub_count_{token}_{i}"
        st.session_state.setdefault(
            sub_count_key,
            len(default_ing.substitutes) if default_ing else 0,
        )

        with st.container(border=True):
            top1, top2, top3 = st.columns([2, 1, 1.2])

            with top1:
                name = ingredient_selector(
                    f"食材 {i + 1}",
                    f"ing_name_{token}_{i}",
                    known,
                    default_ing.name if default_ing else None,
                )
            with top2:
                amount = st.text_input(
                    "用量",
                    value=default_ing.amount if default_ing else "",
                    key=f"ing_amount_{token}_{i}",
                )
            with top3:
                default_importance = (
                    IMPORTANCE_REVERSE[default_ing.importance] if default_ing else "必须有"
                )
                importance_options = list(IMPORTANCE_LABELS)
                importance_label = st.selectbox(
                    "重要程度",
                    importance_options,
                    index=importance_options.index(default_importance),
                    key=f"ing_importance_{token}_{i}",
                )

            substitutes = []
            sub_count = st.session_state[sub_count_key]

            for j in range(sub_count):
                default_sub = (
                    default_ing.substitutes[j]
                    if default_ing and j < len(default_ing.substitutes)
                    else None
                )
                s1, s2 = st.columns(2)
                with s1:
                    sub_name = ingredient_selector(
                        f"替换食材 {j + 1}",
                        f"sub_name_{token}_{i}_{j}",
                        known,
                        default_sub.name if default_sub else None,
                    )
                with s2:
                    default_quality = QUALITY_REVERSE[default_sub.quality] if default_sub else "基本没问题"
                    quality_options = list(QUALITY_LABELS)
                    quality_label = st.selectbox(
                        "替换后的影响",
                        quality_options,
                        index=quality_options.index(default_quality),
                        key=f"sub_quality_{token}_{i}_{j}",
                    )

                note = st.text_input(
                    "替换说明（可选）",
                    value=default_sub.note if default_sub else "",
                    key=f"sub_note_{token}_{i}_{j}",
                )

                if sub_name:
                    substitutes.append(
                        Substitute(
                            name=sub_name.strip(),
                            quality=QUALITY_LABELS[quality_label],
                            note=note.strip(),
                        )
                    )

            x1, x2, _ = st.columns([1, 1, 3])
            with x1:
                if st.button("＋ 替换食材", key=f"add_sub_{token}_{i}", use_container_width=True):
                    st.session_state[sub_count_key] = sub_count + 1
                    st.rerun()
            with x2:
                if sub_count and st.button(
                    "－ 删除替换",
                    key=f"remove_sub_{token}_{i}",
                    use_container_width=True,
                ):
                    st.session_state[sub_count_key] = sub_count - 1
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

    a1, a2, _ = st.columns([1, 1, 3])
    with a1:
        if st.button("＋ 添加食材", key=f"add_ing_{token}", use_container_width=True):
            st.session_state[ingredient_count_key] += 1
            st.rerun()
    with a2:
        if ingredient_count > 1 and st.button(
            "－ 删除最后一项",
            key=f"remove_ing_{token}",
            use_container_width=True,
        ):
            st.session_state[ingredient_count_key] -= 1
            st.rerun()

    st.divider()
    st.subheader("🍳 制作步骤")
    steps = []
    step_count = st.session_state[step_count_key]

    for i in range(step_count):
        default_step = existing.steps[i] if existing and i < len(existing.steps) else ""
        value = st.text_area(
            f"步骤 {i + 1}",
            value=default_step,
            height=80,
            key=f"step_{token}_{i}",
        )
        if value.strip():
            steps.append(value.strip())

    s1, s2, _ = st.columns([1, 1, 3])
    with s1:
        if st.button("＋ 添加步骤", key=f"add_step_{token}", use_container_width=True):
            st.session_state[step_count_key] += 1
            st.rerun()
    with s2:
        if step_count > 1 and st.button(
            "－ 删除最后一步",
            key=f"remove_step_{token}",
            use_container_width=True,
        ):
            st.session_state[step_count_key] -= 1
            st.rerun()

    st.subheader("🐱 黄师傅提醒")
    tips = []
    tip_count = st.session_state[tip_count_key]

    for i in range(tip_count):
        default_tip = existing.tips[i] if existing and i < len(existing.tips) else ""
        value = st.text_input(
            f"提醒 {i + 1}",
            value=default_tip,
            key=f"tip_{token}_{i}",
        )
        if value.strip():
            tips.append(value.strip())

    t1, t2, _ = st.columns([1, 1, 3])
    with t1:
        if st.button("＋ 添加提醒", key=f"add_tip_{token}", use_container_width=True):
            st.session_state[tip_count_key] += 1
            st.rerun()
    with t2:
        if tip_count > 1 and st.button(
            "－ 删除最后一条",
            key=f"remove_tip_{token}",
            use_container_width=True,
        ):
            st.session_state[tip_count_key] -= 1
            st.rerun()

    st.divider()
    save_label = "💾 保存修改" if editing else "🚀 保存并发布到小猫食堂"

    if st.button(save_label, type="primary", use_container_width=True, key=f"save_{token}"):
        errors = []
        if not recipe_name.strip():
            errors.append("请填写菜名。")
        if not ingredients:
            errors.append("至少需要一个食材。")
        if not steps:
            errors.append("至少需要一个制作步骤。")

        if errors:
            for error in errors:
                st.error(error)
            return

        recipe_id = existing.id if existing else f"recipe-{uuid.uuid4().hex[:10]}"
        image_path = save_recipe_image(
            recipe_id,
            image_file,
            existing.image if existing else None,
        )

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

        save_recipe(recipe)
        action = "Update" if editing else "Add"
        success, message = publish_changes(f"{action} recipe: {recipe.name}")

        if success:
            st.session_state["selected_recipe_id"] = None
            st.session_state["admin_page"] = "list"
            st.session_state["editor_nonce"] += 1
            st.success(f"✅ {recipe.name} 已保存。{message}")
            st.rerun()
        else:
            st.warning(f"菜谱已保存，但 GitHub 自动同步失败：{message}")


def help_page() -> None:
    st.title("📚 数据规则")
    st.markdown(
        """
### 菜单管理
- 菜单列表：查看所有已发布菜单。
- 编辑：保持原菜单 ID，不会重新生成重复菜单。
- 删除：删除菜谱 JSON 和对应图片。

### 食材重要程度
- 必须有：缺少并且没有可用替代时，会显示缺关键食材。
- 最好有：没有也能做，但会提醒。
- 有更好：完全可选。

### 替换后的影响
- 基本没问题：很接近原方案。
- 味道会有一点区别：仍可推荐。
- 味道会明显变化：会明确标注风味偏差。
        """
    )


init_state()
sidebar()

page = st.session_state["admin_page"]
if page == "list":
    recipe_list_page()
elif page == "editor":
    editor_page()
else:
    help_page()
