USE ai_novel_platform;

START TRANSACTION;

SET @root_dir = 'E:/ai辅助平台/novels/demo-novel';

INSERT INTO ai_novel_project
(name, genre, premise, style_guide_path, root_dir, status)
VALUES
(
  '示例长篇小说',
  '玄幻 / 权谋',
  '一个被边缘化的少年在王朝与宗门夹缝中寻找自身来历，并逐步发现旧时代灭亡真相。',
  CONCAT(@root_dir, '/world/style-guide.md'),
  @root_dir,
  'active'
);

SET @project_id = LAST_INSERT_ID();

INSERT INTO ai_novel_chapter
(project_id, volume_no, chapter_no, title, outline, summary, draft_path, final_path, status)
VALUES
(
  @project_id,
  1,
  1,
  '雪夜入城',
  '主角在雪夜抵达边境城，遭遇盘查，意外发现通缉令上的图案与自己随身玉牌相同。',
  NULL,
  CONCAT(@root_dir, '/chapters/v01/ch001-draft.md'),
  CONCAT(@root_dir, '/chapters/v01/ch001-final.md'),
  'planned'
);

SET @chapter_1_id = LAST_INSERT_ID();

INSERT INTO ai_novel_entity
(project_id, entity_type, name, alias, description, current_state, detail_path, importance)
VALUES
(
  @project_id,
  'character',
  '沈砚',
  JSON_ARRAY('阿砚'),
  '男主。出身不明，携带一枚残缺玉牌，对旧王朝文字有异常感应。',
  '刚抵达边境城，尚未意识到玉牌牵涉旧朝秘案。',
  CONCAT(@root_dir, '/entities/characters/shen-yan.md'),
  5
),
(
  @project_id,
  'character',
  '陆青禾',
  JSON_ARRAY('青禾'),
  '边境城女医，表面温和，暗中替流亡者传递消息。',
  '尚未与沈砚正式结盟。',
  CONCAT(@root_dir, '/entities/characters/lu-qinghe.md'),
  4
),
(
  @project_id,
  'location',
  '寒鸦城',
  JSON_ARRAY('边境城'),
  '王朝北境重镇，常年风雪，军府、商会和宗门探子混杂。',
  '第一卷主要舞台。',
  CONCAT(@root_dir, '/entities/locations/hanya-city.md'),
  5
);

INSERT INTO ai_novel_plot_thread
(project_id, thread_type, title, description, setup_chapter_id, status, notes_path)
VALUES
(
  @project_id,
  'mystery',
  '残缺玉牌的来历',
  '沈砚随身玉牌与旧王朝密令有关，第一章只露出图案相同这一线索。',
  @chapter_1_id,
  'open',
  CONCAT(@root_dir, '/plot-threads/jade-token.md')
);

INSERT INTO ai_novel_timeline_event
(project_id, chapter_id, event_order, title, description, involved_entities, certainty)
VALUES
(
  @project_id,
  @chapter_1_id,
  1.001,
  '沈砚雪夜入寒鸦城',
  '沈砚抵达寒鸦城，在城门盘查时看到通缉令上的旧朝图案。',
  JSON_ARRAY('沈砚', '寒鸦城'),
  'planned'
);

INSERT INTO ai_novel_task
(project_id, chapter_id, task_type, title, instruction_path, context_path, output_path, status, priority)
VALUES
(
  @project_id,
  @chapter_1_id,
  'write_chapter',
  '写作第 1 卷第 1 章：雪夜入城',
  CONCAT(@root_dir, '/tasks/task-0001-write-chapter-001.md'),
  CONCAT(@root_dir, '/context/context-0001-write-chapter-001.json'),
  CONCAT(@root_dir, '/outputs/ch001-draft.md'),
  'pending',
  1
);

COMMIT;
