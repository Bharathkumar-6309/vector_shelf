import React from 'react'

export default function ProductCard({ product }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-col">
      <div className="bg-gray-100 rounded-md h-36 mb-4 flex items-center justify-center overflow-hidden">
        {product?.image ? (
          <img src={product.image} alt={product.name} className="object-cover w-full h-full" />
        ) : (
          <div className="text-gray-400">No image</div>
        )}
      </div>
      <h3 className="text-sm font-medium text-gray-900 mb-1 line-clamp-2">{product.name}</h3>
      <p className="text-sm text-gray-600 mt-auto">${product.price?.toFixed?.(2) ?? product.price}</p>
    </div>
  )
}
