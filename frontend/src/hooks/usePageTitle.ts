import { createContext, useContext, useEffect, useState } from "react"

interface PageTitleContextType {
  title: string
  setTitle: (title: string) => void
}

export const PageTitleContext = createContext<PageTitleContextType>({
  title: "",
  setTitle: () => {},
})

export const usePageTitle = (title?: string) => {
  const context = useContext(PageTitleContext)

  useEffect(() => {
    if (title) {
      context.setTitle(title)
    }
    return () => {
      if (title) {
        context.setTitle("")
      }
    }
  }, [title, context])

  return context
}

export const usePageTitleState = () => {
  const [title, setTitle] = useState("")
  return { title, setTitle }
}
