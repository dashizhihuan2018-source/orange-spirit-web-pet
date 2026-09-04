const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const targets = [...document.querySelectorAll<HTMLElement>('.section-heading, .blueprint, .media-grid, .workflow li, .download-section')]

if (reduceMotion || !('IntersectionObserver' in window)) {
  targets.forEach(target => target.classList.add('revealed'))
} else {
  targets.forEach(target => target.classList.add('reveal'))
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return
      entry.target.classList.add('revealed')
      observer.unobserve(entry.target)
    })
  }, { threshold: .12 })
  targets.forEach(target => observer.observe(target))
}
