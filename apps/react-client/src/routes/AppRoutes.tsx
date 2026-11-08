import { Navigate, Route, Routes } from 'react-router-dom'
import { MainLayout } from '../components/layout/MainLayout/MainLayout'
import { ArticlePage } from '../pages/ArticlePage'
import { ChatPage } from '../pages/ChatPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { SearchResultsPage } from '../pages/SearchResultsPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ChatPage />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route element={<MainLayout />}>
        <Route path="/search" element={<SearchResultsPage />} />
        <Route path="/articles/:documentId/:articleNumber" element={<ArticlePage />} />
        <Route path="/not-found" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/not-found" replace />} />
      </Route>
    </Routes>
  )
}
