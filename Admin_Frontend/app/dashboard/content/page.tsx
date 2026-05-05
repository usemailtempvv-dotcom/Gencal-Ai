"use client";

import { useState } from 'react';
import { Plus, Edit, Trash2, FileText, Code, BookOpen, X, Bold, Italic, List } from 'lucide-react';

interface Content {
  id: string;
  title: string;
  category: string;
  type: 'Lesson' | 'Prompt' | 'Exercise';
  lastUpdated: string;
  status: 'Published' | 'Draft';
}

const categories = [
  'All Content',
  'Mathematics',
  'Programming',
  'Science',
  'Languages',
  'AI Prompts',
];

const initialContent: Content[] = [
  { id: '1', title: 'Introduction to Calculus', category: 'Mathematics', type: 'Lesson', lastUpdated: '2025-12-09', status: 'Published' },
  { id: '2', title: 'Python Basics Tutorial', category: 'Programming', type: 'Lesson', lastUpdated: '2025-12-08', status: 'Published' },
  { id: '3', title: 'Creative Writing Prompt', category: 'AI Prompts', type: 'Prompt', lastUpdated: '2025-12-09', status: 'Published' },
  { id: '4', title: 'Physics Problem Set', category: 'Science', type: 'Exercise', lastUpdated: '2025-12-07', status: 'Draft' },
  { id: '5', title: 'Spanish Vocabulary', category: 'Languages', type: 'Lesson', lastUpdated: '2025-12-09', status: 'Published' },
  { id: '6', title: 'Code Debug Challenge', category: 'Programming', type: 'Exercise', lastUpdated: '2025-12-06', status: 'Published' },
];

export default function ContentManagementPage() {
  const [content, setContent] = useState<Content[]>(initialContent);
  const [selectedCategory, setSelectedCategory] = useState('All Content');
  const [showEditorModal, setShowEditorModal] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [editingItem, setEditingItem] = useState<Content | null>(null);

  const filteredContent = selectedCategory === 'All Content'
    ? content
    : content.filter(item => item.category === selectedCategory);

  const handleEdit = (item: Content) => {
    setEditingItem(item);
    setEditorContent(`# ${item.title}\n\nEdit your content here...`);
    setShowEditorModal(true);
  };

  const handleDelete = (id: string) => {
    setContent(content.filter(item => item.id !== id));
  };

  const handleSave = () => {
    setShowEditorModal(false);
    setEditorContent('');
    setEditingItem(null);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'Lesson':
        return <BookOpen className="w-4 h-4" />;
      case 'Prompt':
        return <FileText className="w-4 h-4" />;
      case 'Exercise':
        return <Code className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Content Management</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage learning materials, prompts, and course content.</p>
        </div>
        <button
          onClick={() => setShowEditorModal(true)}
          className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add New Content
        </button>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Categories Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-900 rounded-2xl p-4 border border-gray-200 dark:border-gray-800">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Categories</h2>
            <div className="space-y-1">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-200 ${
                    selectedCategory === category
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="lg:col-span-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredContent.map((item) => (
              <div
                key={item.id}
                className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 hover:shadow-xl transition-all duration-200 group"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white">
                      {getTypeIcon(item.type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {item.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{item.category}</p>
                    </div>
                  </div>
                </div>

                {/* Meta Info */}
                <div className="flex items-center gap-4 mb-4">
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full ${
                      item.type === 'Lesson'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                        : item.type === 'Prompt'
                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                        : 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400'
                    }`}
                  >
                    {item.type}
                  </span>
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full ${
                      item.status === 'Published'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                    }`}
                  >
                    {item.status}
                  </span>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-800">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Updated: {item.lastUpdated}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(item)}
                      className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Rich Text Editor Modal */}
      {showEditorModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col border border-gray-200 dark:border-gray-800">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                {editingItem ? `Edit: ${editingItem.title}` : 'Create New Content'}
              </h3>
              <button
                onClick={() => setShowEditorModal(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Toolbar */}
            <div className="flex items-center gap-2 p-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800">
              <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <Bold className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </button>
              <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <Italic className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </button>
              <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <List className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </button>
              <div className="ml-auto flex gap-2">
                <select className="px-3 py-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm">
                  <option>Mathematics</option>
                  <option>Programming</option>
                  <option>Science</option>
                  <option>Languages</option>
                  <option>AI Prompts</option>
                </select>
                <select className="px-3 py-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm">
                  <option>Lesson</option>
                  <option>Prompt</option>
                  <option>Exercise</option>
                </select>
              </div>
            </div>

            {/* Editor Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <textarea
                value={editorContent}
                onChange={(e) => setEditorContent(e.target.value)}
                placeholder="Start writing your content..."
                className="w-full h-full min-h-[400px] bg-transparent border-none focus:outline-none text-gray-900 dark:text-white resize-none font-mono text-sm"
              />
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-800">
              <button
                onClick={() => setShowEditorModal(false)}
                className="px-6 py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:shadow-lg transition-all"
              >
                Save Content
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
