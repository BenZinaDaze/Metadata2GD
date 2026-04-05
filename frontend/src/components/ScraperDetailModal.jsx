import { useEffect, useState } from 'react'
import { tmdbGetDetail } from '../api'
import DetailModal from './DetailModal'

export default function ScraperDetailModal({ item: initialItem, onClose, onToast, onSearchResources }) {
  const [item, setItem] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(true)
  


  useEffect(() => {
    async function loadDetail() {
      setLoadingDetail(true)
      const tmdbId = initialItem.tmdb_id || initialItem.id
      if (!tmdbId) {
        setItem(initialItem)
        setLoadingDetail(false)
        return
      }
      try {
        const res = await tmdbGetDetail(initialItem.media_type, tmdbId)
        if (res.data?.detail) {
          setItem(res.data.detail)
        } else {
          setItem(initialItem)
        }
      } catch(e) {
        setItem(initialItem)
      } finally {
        setLoadingDetail(false)
      }
    }
    loadDetail()
  }, [initialItem])



  if (!initialItem) return null

  // Use initialItem if detail item is not yet loaded for layout placeholder
  const displayItem = item || initialItem

  const headerRight = (
    <button 
      onClick={() => onSearchResources(displayItem)}
      disabled={loadingDetail}
      className="size-10 flex shrink-0 items-center justify-center rounded-full transition-all hover:scale-105 shadow-[0_4px_16px_rgba(200,146,77,0.3)] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      style={{ background: 'linear-gradient(135deg, #e3b778, #c8924d)', color: '#0A1320' }}
      title="检索资源"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
    </button>
  )

  return (
    <DetailModal
      item={displayItem}
      onClose={onClose}
      loadingSlot={loadingDetail}
      headerRightSlot={headerRight}
    />
  )
}
